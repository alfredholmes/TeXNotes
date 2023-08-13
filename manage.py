#!/bin/python3
import sys

import shutil
from LatexZettel import files, database, analysis
import re
import os
import peewee as pw
import datetime


import platform

OPEN_COMMAND = 'xdg-open'

if platform.system() == 'Darwin':
    OPEN_COMMAND = 'open'
elif platform.system() == 'Windows':
    OPEN_COMMAND = 'start'

class Helper:
    """
        Collection of functions for managing a LaTeX Zettelkasten. Each of these functions can be run from the command line by running

        `python manage.py function_name arg1 arg2 ...`

        For example, running 

        `python manage.py newnote note_name`

        executes `Hepler.newnote(note_name)`.

        These can be executed by hand (for now). The plan for the future is to get other applications (eg a text editor) to run these functions.

    """
    renderers = {'pdf': ['pdflatex', ['--interaction=scrollmode']], 'html': ['make4ht', ['-c', '../config/make4ht.cfg', '-']]} # {'format': ['command_line_command', ['list', 'of', 'commandline', 'options']]}

    def help():
        print("""
            Manage the LaTeX slip box. The file manage.py is documented with docstrings, see /docs for detailed information
        """)

    def addtodocuments(filename, reference=""):
        """
            Adds line \externaldocument[reference-]{filename} to documents.tex
            If reference is not supplied then it defaults to, for example, NoteName if filename=note_name
        """
            

        with open('notes/documents.tex', 'a') as f:
            f.write(f'\externaldocument[{reference}-]{{{filename}}}\n')

                

    

    def newnote(note_name, reference_name=""):
        """
            Makes a new note with name note_name [Optional ReferenceName]
            Creates note with name note_name.tex, Second argument is optional and is the name in the reference, defaults to NoteName

            to do: check whether a file already exists etc

        """
        if reference_name == "":
            reference_name = ''.join([w.capitalize() for w in note_name.split('_')])
        
        #see if the note already exists
        try:
            note = database.Note.get(filename=note_name)
            raise ValueError(f'A note with file name {note_name} already exists in the database. If this is not the case then run manage.py synchronize to update the database, and then try again')
            return 
        except pw.OperationalError:
            database.create_all_tables()
        except database.Note.DoesNotExist:
            try: 
                note = database.Note.get(reference=reference_name)
                raise ValueError(f'A note with reference {reference} already exists in the database. If this is not the case then run manage.py synchronize to update the database, and then try again. If the problem persists check the documents.tex file is correctly setup')
                return
            except database.Note.DoesNotExist:
                pass 
    
        Helper.__createnotefile(note_name)
        Helper.addtodocuments(note_name, reference_name)
        #once created, add note to database 
        note = database.Note(filename=note_name, reference=reference_name, created = datetime.datetime.now(), last_edit_date = datetime.datetime.now())
        note.save()



    def list_recent_files(n = 10):
        """
            List the most recently edited files.
        """

        recent_files = Helper.__get_recent_files(int(n))

        for i, f in enumerate(recent_files):
            print(f'{i + 1}:\t', os.path.split(f)[-1][:-4])




    def rename_recent(n = 1):
        """
            Rename the most recent nth file.

        """
        Helper.synchronize()
        n = int(n)

        file = os.path.split(Helper.__get_recent_files(int(n))[n-1])[-1][:-4]

        db_file = database.Note.get(filename=file)
        
        new_name = input(f"Change file name to [{file}]: ") or db_file.filename
        new_reference = input(f"Change reference to [{db_file.reference}]: ") or db_file.reference


        if new_name != db_file.filename:
            Helper.rename_file(db_file.filename, new_name)

        if new_reference != db_file.reference:
            Helper.rename_reference(db_file.reference, new_reference)

    def rename_file(old_filename, new_filename):
        """
            Rename the .tex file, fairly straightforward since only need to change documents.tex
        """
        try:
            with open(f'notes/slipbox/{new_filename}.tex', 'r'):
                pass
            raise ValueError(f'File, {new_filename}.tex already exists')
        except FileNotFoundError:
            pass
        #copy file
        shutil.copy(f'notes/slipbox/{old_filename}.tex', f'notes/slipbox/{new_filename}.tex')

        os.remove(f'notes/slipbox/{old_filename}.tex')

        #change documents.tex
        note = database.Note.get(filename=old_filename)
        note.filename = new_filename

        note.save()

        lines = bytearray()

        with open('notes/documents.tex', 'r') as f:
            for line in f:
                lines.extend(re.sub('\\\\externaldocument\[' + note.reference + '\-\]\{' + old_filename + '\}', '\\\\externaldocument[' + note.reference + '-]{' + new_filename + '}', line).encode())


        with open('notes/documents.tex', 'wb') as f:
            f.write(lines)
        

    def rename_reference(old_reference, new_reference):
        """
            Rename the reference used throughout the whole Zettelkasten. This function changes documents.tex and also any documents that reference this note.
        """

        #function for regex replacement
        Helper.synchronize()
        def replace_text(m):
            if m.group(1) is None and m.group(3) is None:
                return f'\\\\excref{new_reference}'
            elif m.group(1) is None and m.group(3) is not None:
                return f'\\\\excref[{m.group(4)}]{{{new_reference}}}'
            elif m.group(1) is not None and m.group(3) is None:
                return f'\\\\exhyperref{new_reference}'
            elif m.group(1) is not None:
                return f'\\\\exhyperref[{m.group(4)}]{{{new_reference}}}'


        # Update documents.tex

        note = database.Note.get(reference=old_reference)

        lines = bytearray()

        with open('notes/documents.tex', 'r') as f:
            for line in f:
                lines.extend(re.sub('\\\\externaldocument\[' + note.reference + '\-\]\{' + note.filename + '\}', '\\\\externaldocument[' + new_reference + '-]{' + note.filename + '}', line).encode())
        
        with open('notes/documents.tex', 'wb') as f:
            f.write(lines)


        for label in note.labels: 
            backrefs = set()
            for backref in label.referenced_by:
                backrefs.add(backref)
            for backref in backrefs:
                lines = bytearray()
                with open(f'notes/slipbox/{backref.source.filename}.tex', 'r') as f:
                    for line in f:
                        lines.extend(re.sub('\\\\ex(hyper)?(c)?ref(\[([^]]+)\])?\{' + old_reference + '\}', lambda m: replace_text(m), line).encode())

                with open(f'notes/slipbox/{backref.source.filename}.tex', 'wb') as f:
                    f.write(lines)
        
        #update note db
        note.reference = new_reference
        note.save()


    def remove_note(filename):
        """
            Delete a note with given filename
        """
        try:
            note = database.Note.get(filename=filename)
            print('Delete database entry? (y/n)') 
            if Helper.__getyesno():
                note.delete_instance()
        except database.Note.DoesNotExist:
            note = None
            print(f'No note with filename {filename} exists in db')



        with open('notes/documents.tex', 'r') as f:
            lines = f.readlines()
        
        to_delete= []
        for i, line in enumerate(lines):
            m = re.search(f'(\\\\externaldocument\[)(.+?)(\-\]\{{){filename}(\}})', line)
            if m:
                to_delete.append(i)
           
        for i in reversed(to_delete):
            print(f'delete line {lines[i].strip()} from notes/documents.tex? (y/n)')
            if Helper.__getyesno():
                lines.pop(i)
        
        with open('notes/documents.tex', 'w') as f:
            for line in lines:
                f.write(line)


        print(f'Delete notes/slipbox/{filename}.tex? (y/n)')
        if Helper.__getyesno():
            try:
                os.remove(f'notes/slipbox/{filename}.tex')
            except FileNotFoundError:
                print('Error, no such file exists')

    

    def render(filename, format='pdf'):
        """

            Render the LaTeX file. By default renders as a pdf and output is stored in the folder /pdf. The other format option is html, although support is currently experimental.

        """
        import subprocess
        command, options = Helper.renderers[format]
        
        try:
            os.mkdir(format)
        except FileExistsError:
            pass

        
        note = database.Note.get(filename=filename)
        linked_files = set()

        external_documents = ""
        references = set()

        for label in note.labels:
            for link in label.referenced_by:
                source = link.source
                references.add(source)
                linked_files.add(link.source.reference)




        for link in note.references:
            target_note = link.target.note
            if link.target.note.last_build_date_html is not None:
                references.add(target_note) 
      
        #inject external documents 
        if format == 'html':
            for reference in references:
                if reference.last_build_date_html is not None:
                    external_documents += f"\\externaldocument[{reference.reference}-]{{{reference.filename}}}\n"
       
        referenced_by_section = "\\section*{Referenced In}\n\\begin{itemize}\n"
        for reference in linked_files:
            referenced_by_section += f"\\item \\excref{{{reference}}}"

        referenced_by_section += "\\end{itemize}"

        

        os.chdir(format)


        path_to_file = f'../notes/slipbox/{filename}.tex'


        try:
            with open(path_to_file, 'r'):
                pass
        except FileNotFoundError:
            print('No such file!')
            return '', f'Can\'t find {path_to_file}'


        with open(path_to_file, 'r') as f:
            contents = f.read()

        if format == 'pdf':
            options.insert(0, f"--jobname={filename}")
        elif format == 'html':
            options = ['-j', filename] + options + ['"svg"']
            
 

        document = contents.split('\\end{document}')[0]

        if len(linked_files) > 0:
            document += referenced_by_section

        if format == 'html':
            #replace include with preamble_html and inject external documents
            document = document.replace("\\subimport{../template}{preamble.tex}", "\\subimport{../template}{preamble_html.tex}\n" + external_documents)

        document += "\\end{document}"


        process = subprocess.run([command, *options], input=document.encode(), capture_output=True)

        os.chdir('../')

        if format == 'html':
            note.last_build_date_html = datetime.datetime.now()
        elif format == 'pdf':
            note.last_build_date_pdf = datetime.now()
        note.save()
        return process.stdout, process.stderr

        

    def render_all(format='pdf'):
        """
            Function to replace renderallhtml and renderallpdf, rendering notes in a sensible order with regards to dependencies for PDFLaTeX links. Not currently implemented.
        """
        pass

        
    def biber(filename, folder='pdf'):
        """

            Run biber on the render of the note. Folder can be either html or pdf, depending on the format.

        """
        import subprocess
        os.chdir(folder)
        process = subprocess.run(['biber', filename], capture_output=True)
        output, error = process.stdout, process.stderr
        os.chdir('../')

        return output, error
        

    def render_all_html():
        """
            Renderes all the notes using make4ht. Saves output in /html
        """
        import subprocess
        
        notes = Helper.__getnotefiles()
        

        print('render pass 1')
        for note in notes:
            filename = os.path.split(note)[-1][:-4]
            print(f'rendering {filename}...', end='')
            output, error = Helper.render(filename, 'html') 
            print('done')
            print('running biber...', end='')
            output, error = Helper.biber(filename, 'html')
            print('done')
        
        print('render pass 2')
        for note in notes:
            filename = os.path.split(note)[-1][:-4]
            print(f'rendering {filename}...', end='')
            output, error = Helper.render(filename, 'html')
            if error == '':
                print('done')
            else:
                print('\n',error)
       
       
    def render_all_pdf():
        """
            Renderes all the notes using pdflatex. Saves output in /pdf
        """
        import subprocess
        
        notes = Helper.__getnotefiles()
        

        print('render pass 1')
        for note in notes:
            filename = os.path.split(note)[-1][:-4]
            print(f'rendering {filename}...', end='')
            output, error = Helper.render(filename) 
            if error == b'':
                print('done')
                print('running biber...', end='')
                output, error = Helper.biber(filename)
                print('done')
            else:
                print('error!')
                print(error)
        
        print('render pass 2')
        for note in notes:
            filename = os.path.split(note)[-1][:-4]
            print(f'rendering {filename}...', end='')
            output, error = Helper.render(filename)
            if error == '':
                print('done')
            else:
                print('\n',error)

    def synchronize():
        """
            Reads the file documents.tex and adds these files to the database (/slipbox.db), then checks for files in /notes that aren't in the documents
        """
        database.create_all_tables()
        notes = Helper.__getnotefiles()
        notes = [os.path.split(note)[-1][:-4] for note in notes]
        #get all the tracked notes (the ones in documents.tex)
        tracked_notes = {}
        with open('notes/documents.tex', 'r') as f:
            for line in f:
                m = re.search('(\\\\externaldocument\[)(.+?)(\-\]\{)(.+?)(\})', line)
                if m:
                    reference_name = m.group(2)
                    filename = m.group(4)


                    if filename not in notes:
                        print(f'File {filename} with reference {reference_name} missing from notes. Make new note now? (y/n)')
                        if Helper.__getyesno():
                            Helper.__createnotefile(filename)
                            tracked_notes[filename] = reference_name
                            
                    else:
                        tracked_notes[filename] = reference_name

        for filename, reference_name in tracked_notes.items():
            modified = datetime.datetime.fromtimestamp(os.path.getmtime(f'notes/slipbox/{filename}.tex'))
            

            try:
                note = database.Note.get(filename=filename)
                note.last_edit_date = modified
                if note.created is None:
                    note.created = note.last_edit_date

                try:
                    html_render = datetime.datetime.fromtimestamp(os.path.getmtime(f'html/{filename}.html'))
                    note.last_build_date_html = html_render
                except FileNotFoundError as e:
                    #print(f'{filename} is yet to be rendered as html')
                    pass
                
                try:
                    pdf_render = datetime.datetime.fromtimestamp(os.path.getmtime(f'pdf/{filename}.pdf'))
                    note.last_build_date_pdf = pdf_render
                except FileNotFoundError as e:
                    print(f'{filename} is yet to be rendered as pdf')
                


                if note.reference == reference_name:
                    pass #nothing to do
                else:
                    #update note reference to the one in documents.tex, might want to check that this is the right thing to do
                    note.reference = reference_name
                note.save()
            
            except database.Note.DoesNotExist:
                try:
                    note = database.Note.get(reference=reference_name)
                    #update the filename in database, might want to check that this is the right thing to do
                    note.filename = filename
                    note.save()
                except database.Note.DoesNotExist:
                    #create the note if there are no close matches
                    note = database.Note(filename=filename, reference=reference_name, created_at=modified, last_edit_date=modified)
                    note.save()



        for note in notes:
            #add any notes to documents.tex
            if note not in tracked_notes:
                print(f'File {note} not tracked by the file documents.tex. Add to the file now? (y/n)')
                if Helper.__getyesno(): 
                    reference = ''.join([w.capitalize() for w in note.split('_')])
                    print(f'Reference (defaults to {reference}):', end='')
                    new_reference = input()
                    if new_reference != "":
                        reference = new_reference
                    try:
                        database.Note.create(filename=note, reference=reference)
                        Helper.addtodocuments(note, reference)
                    except pw.IntegrityError:
                        print('Error adding note, note already exists in database') 
        
        #add labels
        for note in database.Note:
            try:
                labels = Helper.__getlabels(note)
            except FileNotFoundError:
                #todo: handle this error, note does not exist
                pass
            tracked_labels = [label.label for label in note.labels]
            for label in labels:
                if label not in tracked_labels:
                    database.Label.create(label=label, note=note)
                    print(f'created label {label}')

            #remove extra labels
            for label in note.labels:
                if label.label not in labels:
                    label.delete_instance()
                   
        #add connections

        for note in database.Note: 
            try:
                links = Helper.__getlinks(note)
            except FileNotFoundError:
                #todo: handle error
                pass

            tracked = [(link.target.note.reference, link.target.label) for link in note.references] 
            #add in untracked
            for link in links:
                if link not in tracked:
                    try:
                        label = database.Label.get(note__reference=link[0], label=link[1])
                        link = database.Link.create(target=label, source=note)
                        print(f'created link, {note.filename}, {label.note.filename}, {label}')
                    except database.Label.DoesNotExist:
                        print(f'label in {note.filename} with details {link[0]}, {link[1]} does not exist')

            #remove any that no longer exist
            for link in note.references:
                if (link.target.note.reference, link.target.label) not in links:
                    print(f'link {(link.target.note.reference, link.target.label)} no longer exists, deleting')
                    link.delete_instance()


            

                        
    def list_unreferenced():
        """
            Prints a list of notes that are not referenced in any other note. These might want to be added to the index, for example. 
        """
        import numpy as np
        notes, adj_matrix = analysis.calculate_adjacency_matrix()

        referenced_by = np.sum(adj_matrix, axis=0)
        
        number = 1
        for note, links_from in zip(notes, referenced_by):
            if links_from == 0:
                print(f'{number}: {note.filename}')
                number += 1

    def edit(filename=None):
        """

            Open the note default text editor in the directory /notes/slipbox. If no file is passed then this opens 

        """

        most_recent = Helper.__get_recent_files(1)[0]
        import subprocess
        os.chdir('notes/slipbox')
        if filename is None:
            subprocess.call([OPEN_COMMAND, f'{most_recent.split("/")[2]}'])
        else:
            subprocess.call([OPEN_COMMAND, f'{filename}.tex'])


    def to_md(note_name):
        """            
            Work in progress. Export a LaTeX document note to markdown, and convert references to [[WikiLink]] style references.

        """
        def replace_string(m, md_links):
            replacement = '[['
            label = ''
            if m.group(1) is None and m.group(2) == 'c':
                replacement += md_links[(m.group(5), m.group(4))]
            elif m.group(1) == 'hyper':
                replacement += md_links[(m.group(5), m.group(4))] + '|' + m.group(7)

            print(replacement)

            return replacement + ']]'
        # load the file and convert exhyperref and excref to Wiki links
        file = []
        file_references = []
        with open(f'notes/slipbox/{note_name}.tex', 'r') as f:
            for line in f:
                file.append(line)
                links = re.finditer('\\\\ex?(hyper)?(c)?ref(\[([^]+)\])?\{(.*?)\}', line)
                for link in links:
                    if link.group(4) is None:
                        label = 'note'
                    else:
                        label = link.group(4) 
                    file_references.append((link.group(5), label)) 
                                 
        md_links = {} 
        for ref, tex_label in file_references:
            try:
                note = database.Note.get(reference=ref)
            except database.Note.DoesNotExist:
                note = None

            if tex_label == 'note':
                md_links[(ref, tex_label)] = note.filename
            else:
                md_links[(ref, tex_label)] = f'{note.filename}#{tex_label}'
        new_file = bytearray()
        for line in file:
            new_file.extend((re.sub('\\\\ex(hyper)?(c)?ref(\[([^]]+)\])?\{(.*?)\}(\{(.*?)\})?', lambda m : replace_string(m, md_links), line)).encode())

        import subprocess

        print(new_file)

        p = subprocess.run(["pandoc", "-t", "markdown", "-f", "latex", "-o", f"markdown/{note_name}.md" ], input=new_file, capture_output=True)

        print(p.stdout, p.stderr)


    def export_draft(input_file, output_file=None):
        """
            Exports the export input_file (a file like /export/example.tex containing \ExecuteMetaData calls) and creates a .tex file (by default in /draft/filename.tex) where the \ExecuteMetadata commands are replaced with the body of the notes that they reference.
        """
        if output_file is None:
            try:
                os.mkdir('draft')
            except FileExistsError:
                pass
            filename = input_file.split('/')[-1]
            output_file = f'draft/{filename}'

        output = bytearray()
    
        with open(input_file, 'r') as f:
            for line in f:
                output.extend((re.sub('\\\\ExecuteMetaData\[\.\./([^]]+)\]\{([^}]+)\}', '', line).strip() + '\n').encode())
                external_documents = re.finditer('\\\\ExecuteMetaData\[\.\./([^]]+)\]\{([^}]+)\}', line)
                for document in external_documents:
                    import_file = document.group(1) 
                    tag = document.group(2)
                    with open(import_file, 'r') as in_file:
                        import_text_file = in_file.read()
                        import_text = re.search(f'%<\*{tag}>((.|\n)*?)%</{tag}>', import_text_file)
                        output.extend(import_text.group(1).strip().encode())


        with open(output_file, 'wb') as f:
            f.write(output)





    def __getnotefiles(directory='notes/slipbox'):
        notes = [str(f) for f in files.get_files(directory, '.tex')]
        return notes

    def __createnotefile(filename):
        try:
            os.mkdir('notes')
        except FileExistsError:
            pass

        try:
            os.mkdir('notes/slipbox')
        except FileExistsError:
            pass


        try:
            with open(f'notes/slipbox/{filename}.tex', 'r') as f:
                pass
            print(f'File notes/{filename}.tex already exists, skipping copying the template')
            return
        except FileNotFoundError:
            pass

        
        shutil.copyfile('template/note.tex', f'notes/slipbox/{filename}.tex')
        file = bytearray()
        title = ' '.join([s.capitalize() for s in filename.split('_')])

        with open('template/note.tex', 'r') as f:
            for line in f:
                file.extend((re.sub('\\\\title\{(.*?)\}', '\\\\title{' + title + '}', line)).encode())

        with open(f'notes/slipbox/{filename}.tex', 'wb') as f:
            f.write(file)




    def __getlabels(note):
        file_labels = []
        with open(f'notes/slipbox/{note.filename}.tex') as f:
            for line in f:
                labels = re.search('(\\\\(label|currentdoc)\{)(.*?)(\})', line)
                try:
                    label = labels.group(3)
                    file_labels.append(label)
                except AttributeError:
                    pass

        return file_labels




    def __getlinks(note):
        notes = Helper.__getnotefiles()
        file_references = []
        with open(f'notes/slipbox/{note.filename}.tex') as f:
            for line in f:
                links = re.finditer('\\\\ex(hyper)?(c)?ref(\[([^]]+)\])?\{(.*?)\}', line)
                for link in links:
                    if link.group(4) is None:
                        ref = 'note'
                    else:
                        ref = link.group(4) 
                    file_references.append((link.group(5), ref)) 
        return file_references

    def __gettags():
        notes = Helper.__getnotefiles()
        tags = {}
        for note in notes:
            with open(note) as f:
                lines = f.read().splitlines()
                last_line = lines[-1]
                if re.search("\\\\end\{document\}", last_line) is None:
                    note_tags = [f.lower() for f in last_line.strip().split(",")]
                    for tag in note_tags:
                        tags[tag] = ('notes/'.join(note.split('notes/')[1:]))[:-4]


        print(tags)

    
    
    def __get_recent_files(n = -1):
        files = Helper.__getnotefiles()

        print(len(files))

        if int(n) <= 0:
            n = len(files)
       
        file_dict = {}
        for file in files:
            time = os.path.getmtime(file)
            if time in file_dict:
                file_dict[time].append(file)
            else:
                file_dict[time] = [file]

        ordered = sorted(file_dict, reverse=True)

        
        r = []

        for i, t in zip(range(n), ordered):
            r += file_dict[t]

        return r

                
    def __getyesno():
        while True:
            a = input()
            if a == 'y':
                return True
            elif a == 'n':
                return False
            else:
                print('Please enter either \'y\' or \'n\'')
         

def main(args):
    """
        
        Execute the helper functions from the command line.

    """
    try:
        func = args[1]
    except IndexError:
        print(f"No argument passed, try '{args[0]} help'")
        return

    try: 
        function = getattr(Helper, func)
    except AttributeError:
        print(f"Unregognised command {args[1]}, try 'help' for a list of availlable commands")

    function(*args[2:])




if __name__ == "__main__":
    main(sys.argv)
