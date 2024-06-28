<h1 align="center">
  
<a href="https://github.com/mr-pennyworth/alfred-better-dictionaries/releases/latest/">
  <img src="icon.png" width="16%"><br/>
  <img alt="Download"
       src="https://img.shields.io/github/downloads/mr-pennyworth/alfred-better-dictionaries/total?color=purple&label=Download"><br/>
</a>
  Better Dictionaries
</h1>
Better search and live previews for built-in macOS dictionaries.

### Features
 - IPA (phonetic) pronunciations:
   Press `⌘↩` to hear the pronunciation.
 - In-Alfred live previews with colors that
   automatically adapt to Alfred's theme:
   ![](images/auto-theme.png)

 - Reverse search:
   ![](images/reverse-search.png)

 - More relevant search results:  
   left: macOS/Alfred built-in search, right: BetterDict
   ![](images/built-in-vs-workflow.png)

 - If one word has multiple, unrelated meanings with different
   origin, they are showed as diffrent entries
   (in the above example, see "arm" has two entries at the top) 

 - Import any compatible dictionary


### Importing a Dictionary
After importing the workflow, type `.dict-import` into Alfred.
![](images/import-any.png)
Select the dictionary you want to import.  


### Dictionary-specific Keywords and Hotkeys
After a dictionary is imported, a script filter and a hotkey trigger
is automatically created into the workflow editor.  

 - Freshly-installed workflow without any imported dictionaries:
   ![](images/before-import.png)

 - Two hotkeys and keyword triggers each automatically added after importing
   two dictionaries. They come pre-labeled with dictionary names:
   ![](images/after-import.png)

 - This allows you to assign hotkeys and keywords for specific dictionaries.
   For example, below you can see how I have manually assigned keywords
   `thesaurus` and `defn` to the thesaurus and dictionary respectively.
   In addition, I can trigger the dictionary search using `⌃⌥⌘D`.  
   ![](images/example-assignment.png)


### Word Lookup
You can use the hotkeys/keywords created above for directly searhcing
specific dictionaries. That's the recommended way for dictionaries
that you use frequently.

For the infrequently used dictionaries for which you haven't assigned
any hotkeys/keywords, follow this:
 1. Type `lookup` into Alfred. You'll see a list of all dictionaries
    imported into BetterDict.
    ![](images/lookup-imported.png)
 2. Select the dictionary to search, and type the search query.


### Notes and Warnings
 - Importing a dictionary could take as much as 30 minutes
   on old machines or if there's significant CPU activity from other apps.

 - After each mac restart, for the first time when you run
   the workflow, expect a comparatively slower search.
   Subsequent searches should be instant.

 - This workflow takes a LOT of space on disk. Take a look at the comparison:
   ```markdown
   # Built-in dictionaries
   Oxford American Writer's Thesaurus:  7 MB
   New Oxford American Dictionary:     36 MB
   
   # After importing into BetterDict
   Oxford American Writer's Thesaurus: 101 MB (html files)
   New Oxford American Dictionary:     442 MB (html files)
   Combined search index of these two: 730 MB (apart from html)
   ```
