# LaTeX-Zettel - Zettelkasten written with LaTeX.
Zettelkasten or Slip box with notes written in LaTeX. 

### Getting Started

See [wiki/getting started](https://github.com/alfredholmes/LaTeX-Zettel/wiki/Getting-Started) for instructions. See [/docs/manage.html](https://htmlpreview.github.io/?https://github.com/alfredholmes/LaTeX-Zettel/blob/main/docs/manage.html) for documentation on the helper sript manage.py.

### Mailing List

To receive email updates about new features and general information about the project, subscribe to the mailing list [here](https://www.freelists.org/list/latexzettel) or send an email with subject 'subscribe' to latexzettel-request@freelists.org.

### Current Features

* [Internote referencing commands](https://github.com/alfredholmes/LaTeX-Zettel/wiki/Referencing-Other-Notes) - render Zettelkasten with PDFLaTeX or make4ht and get clickable hyperlinks in the PDFs and html pages.
* [Biber support](https://github.com/alfredholmes/LaTeX-Zettel/wiki/Biber-Support) for citations (works well with, for example, Zotero auto export).
* [Helper scripts](https://github.com/alfredholmes/LaTeX-Zettel/wiki/Creating,-Deleting-and-Renaming-Notes) to create new notes from LaTeX templates
* Automated analysis of the Zettelkasten - creates a database from the notes with details of the connections between notes.
* Native python 'network view' of Zettelkasten ([see here](https://github.com/alfredholmes/LaTeX-Zettel/wiki/Network-View)).
* Ability to export multiple notes into a LaTeX document ([see here](https://github.com/alfredholmes/LaTeX-Zettel/wiki/Export-Notes-as-Latex-Document)). 
* [PDF and HTML rendering](https://github.com/alfredholmes/LaTeX-Zettel/wiki/Compiling-Notes)

### Planned Features

* Markdown support with Pandoc
* Customizable templates, and different templates for different notes
* Draw a path on the network view to write a draft of a paper
* Import notes from an existing .tex file - split up already written documents into atomic notes by adding comments to the .tex file that describe the desired notes.


### Why Do This?

This is primarily intended for academics who write papers in LaTeX and want to write notes using the Zettelkasten method that are easily exportable into a full LaTeX document. The other benefits are being able to define theorem environments and using biber or bibtex reference management. This repository is essentially a template to start a new slip box. There is a python script `manage.py` that adds a few functions but you could do this all in latex.


### How to use

See [the wiki](https://github.com/alfredholmes/LaTeX-Zettel/wiki) for detailed usage instructions.

There are three main folders. `/notes`, `/template` and `/pdf`. This assumess that you want to render your notes as `pdf` documents rather than as `html` (`html` rendering also works, replacing `pdflatex` with `make4ht` but there are sometimes some issues with `hyperref` and `xr-hyper` which can be fixed by adding the flag `-c ../config/make4ht.cfg`). Inside `/notes` is where the `.tex` documents get stored. The example notes import the file `/template/preamble` which contains various package imports. The most important part of `/template/preamble.tex` is the importing of the file `/notes/documents.tex` which contains all the `\externaldocument` declarations that will allow `\cref` to reference equations in other documents. Note that the second parameter in the `\externaldocument` command is the name of the file that you want to reference. This is actually refers to the `document_name.aux`, which contains all the referencing information, rather than the `.tex` file. Hence this file name parameter should match the directory structure of the output `pdf`s, not the directory structure of your `.tex` documents. To allow all the notes to use the same `/documents.tex` it is most straightforward to render the `pdf`s from inside the `/pdf` directory. So to render notes using `pdflatex` run
```
$ cd pdf
$ pdflatex ../notes/path_to_note.tex 
```
If note `A` references note `B`, then you'll have to render `B` before `A` for the hyperlinks to work correctly.
    
Now you will have two pdfs (and a load of LaTeX build files) which give a basic example of the setup.

#### Adding New Notes 

To add a new note simply run

`$ ./manage.py newnote note_name [optional cref name, defaults to NoteName = name.split('_') then capitalized and concatenated]`.

this just copies the note template into the `/notes/slipbox/` folder, saving it as `new_note.tex` and adds the line 
```Latex
\externaldocument[NewNote-]{new_note}
```
to `/notes/documents.tex`. Any labels from the note will be able to be referenced from other notes using the command 
```
\excref[reference label]{NewNote}
```
which is defined in `/template/preamble.tex`. This will use `cref` to generate the label and insert `\texttt{NewNote/}` before it. Using just `\cref{NewNote-reference label}` use the default `cref` to render the reference to the label, and so willl not include the document name. To add custom text to the external reference there is the command

```
\exhyperref[reference label]{NewNote}{hyperlink text}
```
also defined in `/template/preamble.tex`. This creates a hyperlink to the item labelled `reference label` in `new_note.tex` with the text `hyperlink text`. If the optional parameter is ommited then `\exhyperref` and `\excref` will reference the label `note` which in the default template is inserted just after the title.

### `manage.py` helper script

See [/docs/manage.html](https://htmlpreview.github.io/?https://github.com/alfredholmes/LaTeX-Zettel/blob/main/docs/manage.html) for documentation.




