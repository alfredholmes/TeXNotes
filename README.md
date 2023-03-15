# LaTeX-Zettle
Zettelkasten or Slip box with notes written in LaTeX

### Why Do This?

This is primarily intended for academics who write papers in LaTeX and want to write notes using the Zettelkasten method that are easily exportable into a full LaTeX document. The other benefits are being able to define theorem environments and using biber or bibtex reference management. This repository is essentially a template to start a new slip box. There is a python script `manage.py` that adds a few functions but you could do this all in latex.


### How to use

    There are three main folders. `/notes`, `/template` and `/pdf`. This assumess that you want to render your notes as `pdf` documents rather than as `html` (`html` rendering also works, replacing `pdflatex` with `make4ht` but there are sometimes some issues with `hyperref` and `xr-hyper`). Inside `/notes` is where the `.tex` documents get stored. The example notes import the file `/template/preamble` which contains various package imports. The most important part of `/template/preamble.tex` is the importing of the file `/documents.tex` which contains all the `\externaldocument` declarations that will allow `\cref` to reference equations in other documents. Note that the second parameter in the `\externaldocument` command is the name of the file that you want to reference. This is actually refers to the `document_name.aux`, which contains all the referencing information, rather than the `.tex` file. Hence this file name parameter should match the directory structure of the output `pdf`s, not the directory structure of your `.tex` documents. To allow all the notes to use the same `/documents.tex` it is most straightforward to render the `pdf`s from inside the `/pdf` directory. So to render the example notes simply run
    ```
    $ cd pdf
    $ pdflatex ../notes/example_note.tex
    $ pdflatex ../notes/referencing_example.tex
    $ pdflatex ../notes/example_note.tex
    $ pdflatex ../notes/referencing_example.tex
    
    ```
    
Now you will have two pdfs (and a load of LaTeX build files) which give a basic example of the setup.

#### Adding New Notes 

To add a new note simply copy the note template into the notes folder and rename it. Say for example  to `new_note.tex`. Now add the line 
```Latex
\externaldocument{NewNote-}{new_note}
```
and that's it. Any labels from the note will be able to be referenced from other notes using the command
```
\excref{NewNote}{reference label}
```
This just wraps the `\cref{NewNote-reference label}` in a hyperlink containing the name of the note.


### `manage.py` helper scripts

The `manage.py` python script contains shortcuts for many frequently executed actions. These include

`$ ./manage.py createnote note_name [optional cref name, defaults to NoteName = name.split('-') then capitalized and concatenated]`.

This executes the procedure described in [Adding New Notes].

`$./manage.py pdf_changed$`

Run `pdflatex` on all notes that have been updated, and then on files which link to these updated files.

`$./manage.py pdf_live [seconds between updates]$`.

Continuously apply `pdf_changed`, checking for updates every second.
