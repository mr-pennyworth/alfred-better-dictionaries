# -*- coding: utf-8 -*-

import glob
import json
import os
import re
import shutil
import sys
import time
import typing
from base64 import b16encode
from collections import defaultdict
from struct import unpack
from subprocess import *

import click
import meilisearch
from bs4 import BeautifulSoup

import alfred
import appledict
import plist
from ProgressBar import IndefiniteProgressBar
from ProgressBar import run_parallely_with_progress_bar
from WorkflowGraph import WorkflowGraph

HOME = os.path.expanduser("~")
SEARCH_IP = os.environ.get("SEARCH_IP", "127.0.0.1")
SEARCH_PORT = os.environ.get("SEARCH_PORT", "6789")
WORKFLOW_DIR = alfred.get_workflow_dir()
WORKFLOW_ID = plist.read(f"{WORKFLOW_DIR}/info.plist")["bundleid"]
DEFAULT_WORKFLOW_DATA_DIR = alfred.default_workflow_data_dir(WORKFLOW_ID)


def noop():
    pass


def read_int(f: typing.BinaryIO) -> int:
    return unpack("i", f.read(4))[0]


def get_word_defs_map(dict_data_path):
    """returns a dict where key is the word
    and value is a list of its definitions."""
    word_to_defs_map = defaultdict(list)

    dict_body = appledict.DictBody(dict_data_path)
    for defn in dict_body.definitions():
        # Example XML defn opening tag:
        # <d:entry
        #   xmlns:d=".apple.com/DTDs/DictionaryService-1.0.rng"
        #   id="m_en_gbus0134270"
        #   d:title="apple"
        #   class="entry">
        # The principled way to find the word being defined
        # would be to parse the XML and then get 'd:title' from it,
        # however, that's too slow, so we resort to regex matching.
        word = re.search('d:title="(.*?)"', defn).group(1)
        word_to_defs_map[word].append(defn)
    return word_to_defs_map


def base16(input_str):
    return b16encode(input_str.encode("utf-8")).decode("utf-8")


def filename_defn_pairs(word, defns):
    """for <word> and its <n>th definition,
    we are going to create an HTML file whose name is
    base16(<word><n>).html and content is the definition

    we do this as we need some sort of 'safe' encoding as words might
    contain characters that can't be part of a filename. also, we don't
    want collisions on case-insensitive filesystems.

    returns list of (filename, definition)
    """
    return [
        (f'{base16(f"{word}{i}")}.html', defn) for i, defn in enumerate(defns)
    ]


def create_html_file(word, definitions, html_dir):
    """for <word> and its nth definition,
    create an HTML file whose name is
    base16(<word>n).html and content is the definition

    need some sort of 'safe' encoding as words might contain
    characters that can't be part of a filename. also, we don't
    want collisions on case-insensitive filesystems.
    """
    for filename, definition in filename_defn_pairs(word, definitions):
        with open(f"{html_dir}/{filename}", "wb") as f:
            f.write(
                f"""<!DOCTYPE html>
        <html lang="en">
          <head>
            <meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>
            <link rel="stylesheet" href="dict-entry.css">
          </head>
          <body> {definition} </body>
        </html>""".encode(
                    "utf-8"
                )
            )


def create_html_files(word_defs_map_items, html_dir):
    title = "Creating HTML files..."
    run_parallely_with_progress_bar(
        items=word_defs_map_items,
        func=lambda x: create_html_file(x[0], x[1], html_dir),
        msgfunc=lambda x: x[0],
        title=title,
    )

    os.link(
        src=f"{WORKFLOW_DIR}/dict-entry.css",
        dst=f"{html_dir}/dict-entry.css",
    )


class AccumulatedIndexer:
    def __init__(self, index):
        self.items = []
        self.index = index

    def add(self, items):
        self.items.extend(items)

    def finish(self):
        task_info = self.index.add_documents(self.items)

        def status():
            return self.index.get_task(task_info.task_uid).status

        ipb = IndefiniteProgressBar(title="Waiting for index to be ready...")
        while (s := status()) != "succeeded":
            ipb.update(message="")
            time.sleep(2)
        ipb.finish()


def build_index(word_defs_map_items, dict_id, db_path, html_dir):
    index = create_index(dict_id, db_path)
    title = "Building index for instant search..."

    def make_alfred_items(word, defs):
        return [
            make_alfred_item(word, filename, definition, html_dir)
            for filename, definition in filename_defn_pairs(word, defs)
            if word != ""
        ]

    run_parallely_with_progress_bar(
        items=word_defs_map_items,
        func=lambda word_n_defs: make_alfred_items(*word_n_defs),
        msgfunc=lambda word_n_defs: word_n_defs[0],
        accumulator=AccumulatedIndexer(index),
        title=title,
    )


def make_alfred_item(word, filename, definition, html_dir):
    soup = BeautifulSoup(definition, "lxml")
    fulltext = soup.get_text()
    snippet = fulltext
    snippet_div = soup.find(attrs={"d:def": "1"})
    if snippet_div is not None:
        snippet = snippet_div.get_text()

    # forms of a word typically include:
    # plural forms of a noun: (mouse, mice)
    # intensifiers for odjectives: (good, better, best)
    # past-tense variations of verbs: (fly, flew, flown)
    forms = ""
    forms_div = soup.find(attrs={"class": "infg"})
    if forms_div is not None:
        forms = forms_div.get_text()

    html_path = f"{html_dir}/{filename}"
    item = {
        "arg": html_path,
        "title": word,
        "id": filename.split(".")[0],
        "forms": forms,
        "subtitle": forms + snippet,
        "fulltext": fulltext,
        "quicklookurl": html_path,
    }

    ipa_div = soup.find(attrs={"d:prn": "IPA solitary"})
    if ipa_div is None:
        ipa_div = soup.find(attrs={"d:prn": "IPA"})
    if ipa_div is None:
        return item

    pronunciation = ipa_div.get_text().split(",")[0]

    item["subtitle"] = "[⌘: 🗣] " + item["subtitle"]
    item["mods"] = {
        "cmd": {"arg": pronunciation, "subtitle": "🗣 " + pronunciation}
    }

    return item


def dict_info(dict_path):
    return plist.read(f"{dict_path}/Contents/Info.plist")


def all_dict_paths():
    dict_paths = []
    dict_globs = [
        "/System/Library/AssetsV2/**/*.dictionary",
        "/Library/Dictionaries/**/*.dictionary",
        f"{HOME}/Library/Dictionaries/**/*.dictionary",
    ]
    for dict_glob in dict_globs:
        dict_paths.extend(glob.glob(dict_glob, recursive=True))
    return [
        dict_path
        for dict_path in dict_paths
        if any(
            map(
                os.path.exists,
                [
                    f"{dict_path}/Contents/Resources/Body.data",
                    # While all dictionaries that come bundled with macOS store Body.data
                    # in the Contents/Resources folder,
                    # https://agiletortoise.com/terminology/mac/ stores the Body.data
                    # directly in the Contents folder.
                    f"{dict_path}/Contents/Body.data",
                ],
            )
        )
    ]


def get_dict_id(info):
    # meilisearch index doesn't allow periods in name
    return info["CFBundleIdentifier"].replace(".", "-")


def get_dict_name(info):
    return info.get(
        "CFBundleDisplayName",
        info.get(
            "CFBundleName",
            info["CFBundleIdentifier"],
        ),
    )


def create_workflow_objects(dict_name, dict_id):
    wf = WorkflowGraph(f"{WORKFLOW_DIR}/info.plist")

    # Functional:
    junction = wf.newJunction()
    hotkey = wf.newHotkey(note=dict_name)
    fallback_search = wf.newFallbackSearch(
        note=dict_name,
        title=f"search {dict_name}",
    )
    script_filter = wf.newBashScriptFilter(
        note=dict_name,
        title=f"search {dict_name}",
        script=(
            "open -g ./AlfredExtraPane.app\n\n"
            'query="$1"\n\n'
            f'./search.sh "$query" "{dict_id}"'
        ),
    )
    router = wf.getObjWithLabel("router")
    router_output = wf.addOutputToRouter(router, output=dict_id)
    ipa_player = wf.getObjWithLabel("Play pronunciation audio")
    html_opener = wf.getObjWithLabel("Open definition in browser")
    wf.connect(src=hotkey, dst=script_filter)
    wf.connect(src=fallback_search, dst=script_filter)
    wf.connect(src=junction, dst=script_filter)
    wf.connect(src=script_filter, dst=ipa_player, mod=wf.CMD)
    wf.connect(src=script_filter, dst=html_opener)
    wf.connect(src=router, dst=junction, src_out=router_output)

    # Presentational:
    dummy_junction = wf.getObjWithLabel("dummy junction")
    dummy_hotkey = wf.getObjWithLabel("dummy hotkey")
    dummy_fallback_search = wf.getObjWithLabel("dummy fallback search")
    dummy_script_filter = wf.getObjWithLabel("dummy script filter")

    row_count = wf.getOutputCount(router)
    VERT_OFFSET = 180 * (row_count - 1)
    wf.setX(junction, wf.x(dummy_junction))
    wf.setY(junction, wf.y(dummy_junction) + VERT_OFFSET)

    wf.setX(hotkey, wf.x(dummy_hotkey))
    wf.setY(hotkey, wf.y(dummy_hotkey) + VERT_OFFSET)

    wf.setX(fallback_search, wf.x(dummy_fallback_search))
    wf.setY(fallback_search, wf.y(dummy_fallback_search) + VERT_OFFSET)

    wf.setX(script_filter, wf.x(dummy_script_filter))
    wf.setY(script_filter, wf.y(dummy_script_filter) + VERT_OFFSET)

    wf.setY(html_opener, wf.y(script_filter))

    wf.save()


def import_dict(dict_path, import_base_dir):
    info = dict_info(dict_path)
    dict_id = get_dict_id(info)
    dict_name = get_dict_name(info)

    data_path = f"{dict_path}/Contents/Resources/Body.data"
    if not os.path.exists(data_path):
        # https://agiletortoise.com/terminology/mac/ stores the Body.data directly
        # in the Contents folder (and not in Contents/Resources folder).
        data_path = f"{dict_path}/Contents/Body.data"

    dest_dir = f"{import_base_dir}/{dict_id}"
    dest_html_dir = f"{dest_dir}/html"
    db_path = f"{import_base_dir}/db"

    if not is_search_server_up():
        start_search_server(db_path)

    os.makedirs(dest_html_dir, exist_ok=True)

    word_defs_map = get_word_defs_map(data_path)
    word_defs_map_items = word_defs_map.items()
    create_html_files(word_defs_map_items, dest_html_dir)
    build_index(word_defs_map_items, dict_id, db_path, dest_html_dir)

    imported = {"items": []}
    imported_json_path = f"{import_base_dir}/imported.json"

    if os.path.exists(imported_json_path):
        with open(imported_json_path) as f:
            imported = json.load(f)

    imported["items"].append({"title": dict_name, "arg": dict_id})

    create_workflow_objects(dict_name, dict_id)
    with open(imported_json_path, "w") as f:
        json.dump(imported, f, indent=2)


def is_search_server_up():
    return call(["pgrep", "alfred-dict-server"], stdout=DEVNULL) == 0


def start_search_server(db_path):
    with open(f"{db_path}.log", "wb") as logfile:
        cmd = [
            f"{WORKFLOW_DIR}/alfred-dict-server",
            "--db-path",
            db_path,
            "--http-addr",
            f"{SEARCH_IP}:{SEARCH_PORT}",
            "--http-payload-size-limit",
            "1000000000",
        ]
        Popen(cmd, stdout=logfile, stderr=logfile)


def search_client(db_path):
    if not is_search_server_up():
        start_search_server(db_path)
    while not is_search_server_up():
        time.sleep(0.01)
    return meilisearch.Client(f"http://{SEARCH_IP}:{SEARCH_PORT}")


def create_index(dict_id, db_path):
    db = search_client(db_path)
    task_info = db.create_index(dict_id)
    db.wait_for_task(task_info.task_uid, timeout_in_ms=10000)
    index = db.get_index(dict_id)
    index.update_searchable_attributes(
        [
            "title",
            "forms",
            "subtitle",
            "fulltext",
        ]
    )
    index.update_ranking_rules(
        [
            "exactness",
            "attribute",
            "typo",
            "words",
            "proximity",
        ]
    )
    index.update_displayed_attributes(
        [
            # everything except id, forms, and fulltext
            "arg",
            "mods",
            "title",
            "subtitle",
            "quicklookurl",
        ]
    )
    return index


def list_unimported_dicts(import_base_dir) -> list[alfred.Item]:
    alfreditems = []

    imported = []
    imported_json_path = f"{import_base_dir}/imported.json"

    if os.path.exists(imported_json_path):
        with open(imported_json_path) as f:
            imported = [i["title"] for i in json.load(f)["items"]]

    for dict_path in all_dict_paths():
        try:
            info = dict_info(dict_path)
            dict_name = get_dict_name(info)
            if dict_name in imported:
                continue
            alfreditems.append(alfred.Item(title=dict_name, arg=dict_path))
        except Exception as e:
            print(f'Unable to process "{dict_path}": {e}', file=sys.stderr)
    return alfreditems


@click.group()
def main():
    pass


@main.command()
@click.argument(
    "workflow_data_dir",
    type=click.Path(exists=True, file_okay=False, resolve_path=True),
    envvar="alfred_workflow_data",
    default=DEFAULT_WORKFLOW_DATA_DIR,
)
def list_unimported(workflow_data_dir: str):
    unimported = list_unimported_dicts(workflow_data_dir)
    print(json.dumps({"items": [d.as_dict() for d in unimported]}, indent=2))


@main.command(name="import")
@click.argument(
    "dict_path",
    type=click.Path(exists=True, file_okay=False, resolve_path=True),
)
@click.argument(
    "workflow_data_dir",
    type=click.Path(exists=True, file_okay=False, resolve_path=True),
    envvar="alfred_workflow_data",
    default=DEFAULT_WORKFLOW_DATA_DIR,
)
def import_(dict_path: str, workflow_data_dir: str):
    import_dict(dict_path, workflow_data_dir)


@main.command()
@click.argument(
    "workflow_data_dir",
    type=click.Path(exists=True, file_okay=False, resolve_path=True),
    envvar="alfred_workflow_data",
    default=DEFAULT_WORKFLOW_DATA_DIR,
)
def factory_reset(workflow_data_dir: str):
    shutil.rmtree(workflow_data_dir)
    shutil.copy(f"{WORKFLOW_DIR}/info.plist", f"{WORKFLOW_DIR}/info.plist.bkp")
    shutil.copy(f"{WORKFLOW_DIR}/info.plist.orig", f"{WORKFLOW_DIR}/info.plist")
    os.mkdir(workflow_data_dir)


if __name__ == "__main__":
    main()
