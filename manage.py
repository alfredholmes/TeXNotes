#!/bin/python3
import sys

import shutil
from LatexZettel import files, database 
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
    renderers = {'pdf': ['pdflatex', ['--interaction=scrollmode']], 'html': ['make4ht', ['-um', 'draft', '-c', os.path.join('..', 'config', 'make4ht.cfg'), '-']]} # {'format': ['command_line_command', ['list', 'of', 'commandline', 'options']]}

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



    def newnote_md(note_name, reference_name=""):
        """
            Creates a new markdown note with the given title. Otherwise, same functionality as Helper.newnote()
        """
        Helper.newnote(note_name, reference_name, extension='md')



    def newnote(note_name, reference_name="", **kwargs):
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
        
        try: 
            ext = kwargs['extension']
        except KeyError:
            ext = 'tex'
        Helper.__createnotefile(note_name, ext)
        Helper.addtodocuments(note_name, reference_name)
        #once created, add note to database 
        note = database.Note(filename=note_name, reference=reference_name, created = datetime.datetime.now(), last_edit_date = datetime.datetime.now())
        note.save()

    def newproject(dir_name, filename=None):
        """
            Creates a project folder (for exporting notes) and copies the project.tex file into the folder
        """

        try:
            os.mkdir('projects')
        except FileExistsError:
            pass


        try:
            dirpath = os.path.join('projects', dir_name)
            os.mkdir(dirpath)
        except FileExistsError:
            raise Exception('Error: project directory already exists')

        if filename is None: 
            filename = f'{dir_name}.tex'

        template = os.path.join('template', 'project.tex')
        tex_file = os.path.join(dirpath, filename)
        shutil.copyfile(template, tex_file)





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
                return f'\\excref{new_reference}'
            elif m.group(1) is None and m.group(3) is not None:
                return f'\\excref[{m.group(4)}]{{{new_reference}}}'
            elif m.group(1) is not None and m.group(3) is None:
                return f'\\exhyperref{new_reference}'
            elif m.group(1) is not None:
                return f'\\exhyperref[{m.group(4)}]{{{new_reference}}}'


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


    def sync_md():
        markdown_files = files.get_files(os.path.join('notes', 'md'), 'md')
        sb_file_names = {os.path.basename(f)[:-3]: "_".join([s for s in os.path.basename(f).split(" ")])[:-3] for f in markdown_files}
        print('Warning: this may overwrite any files in notes/slipbox that share their filename with a file in notes/md. Do you wish to continue?')
        if not Helper.__getyesno():
            return
        tracked_note_files = [note.filename for note in database.Note]
        print(tracked_note_files)
        for file in markdown_files:
            filename = os.path.basename(file)[:-3]
            if sb_file_names[filename] not in tracked_note_files:
                reference_name = ''.join([w.capitalize() for w in sb_file_names[filename].split('_')])
                note = database.Note(filename=sb_file_names[filename], reference=reference_name, created = datetime.datetime.now(), last_edit_date = datetime.datetime.now())
                note.save()
                Helper.addtodocuments(sb_file_names[filename], reference_name)
        
        for file in markdown_files:
            filename = os.path.basename(file)[:-3]
            sb_file = sb_file_names[filename]
            print(sb_file)
            try: 
                edit_delta = os.path.getmtime(file) - os.path.getmtime(os.path.join('notes', 'slipbox', f'{sb_file}.tex'))
            except FileNotFoundError:
                edit_delta = 1

            #if edit_delta > 0:
            if edit_delta > 0: 
                #change all the links in the document
                def md_name_to_reference(match):
                    filename = m.group(1)
                    sb_name = '_'.join(filename.split(' '))
                    return database.Note.get(sb_name).reference


                with open(file, 'r') as f:
                    file_contents = f.read()
                regex = "\[\[([^{\#\]\|}]+)\]\]"
                text = re.sub(regex, lambda m: f"\\excref{{{md_name_to_reference(m)}}}", file_contents)

                regex = "\[\[([^{\#\]\|}]+)\#\^?([A-Za-z0-9\-\_]+)\]\]"

                text = re.sub(regex, lambda m: f"\\excref[{m.group(2)}]{{{md_name_to_reference(m)}}}", text)


                regex = "\[\[([^{\#\]\|}]+)\|([^]]+)\]\]"
                text = re.sub(regex, lambda m: f"\\exhyperref{{{md_name_to_reference(m)}}}{{{m.group(2)}}}", text)

                regex = "\[\[([^{\#\]\|}]+)\#\^?([A-Za-z0-9\-\_]+)\|([^]]+)\]\]"
                text = re.sub(regex, lambda m: f"\\exhyperref[{m.group(2)}]{{{md_name_to_reference(m)}}}{{{m.group(3)}}}", text)

                print(text)

                import subprocess 
                command = 'pandoc' 
                options = ['-o', os.path.join('notes', 'slipbox', f'{sb_file}.tex')]
                options += ['-s', '-t', 'latex', '--lua-filter=pandoc/filter.lua', '--template=pandoc/template.tex', '--metadata-file=pandoc/defaults.yaml', "-M", f"title={filename}"]
                process = subprocess.run([command, *options], input=text.encode(), capture_output=True)

                if process.returncode != 0:
                    print('pandoc error:', process.stderr)

                print(process.stdout)

    def render(filename, format='pdf', biber=False):
        """

            Render the LaTeX file. By default renders as a pdf and output is stored in the folder /pdf. The other format option is html, although support is currently experimental.

        """

        if biber:
            Helper.render(filename, format, False)
            Helper.biber(filename)

        import subprocess
        command, options = Helper.renderers[format]
        options = list(options)

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


        path_to_file = os.path.join('..', 'notes', 'slipbox', f'{filename}.tex') 


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
            options = ['-j', filename] + options + ['"svg-"']
            #options = ['-j', filename] + options



        document = contents.split('\\end{document}')[0]

        if len(linked_files) > 0:
            document += referenced_by_section

        if format == 'html':
            #replace include with preamble_html and inject external documents
            document = document.replace("\\subimport{../template}{preamble.tex}", "\\subimport{../template}{preamble_html.tex}\n" + external_documents)

        document += "\\end{document}"

        process = subprocess.run([command, *options], input=document.encode(), capture_output=True)
        os.chdir('..')

        if process.returncode != 0:
            print('Failed to compile', process.stderr) #TODO: Exceptions
            return process


        if format == 'html':
            note.last_build_date_html = datetime.datetime.now()
        elif format == 'pdf':
            note.last_build_date_pdf = datetime.datetime.now()
        note.save()

        return process



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
            process = Helper.render(filename, 'html') 
            print('done')
            print('running biber...', end='')
            output, error = Helper.biber(filename, 'html')
            print('done')

        print('render pass 2')
        for note in notes:
            filename = os.path.split(note)[-1][:-4]
            print(f'rendering {filename}...', end='')
            process = Helper.render(filename, 'html')
            if process.returncode == 0:
                print('done')
            else:
                print('\n',process.stderr)


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


    def render_updates(format='pdf'):
        updated, new_links, run_biber = Helper.synchronize()



        for note in database.Note:
            if note in updated:
                continue
            if format == 'pdf':
                if note.last_build_date_pdf is None or note.last_edit_date > note.last_build_date_pdf:
                    updated.append(note)
                    run_biber[note] = True
                    #fix reference in
                    new_links.extend([r for r in note.references])
            elif format == 'html':
                if note.last_build_date_html is None or note.last_edit_date > note.last_build_date_html:
                    updated.append(note)
                    run_biber[note] = True
                    #fix referenced in
                    new_links.extend([r for r in note.references])


        #render the updated files
        for note in updated:
            print(f'Rendering {note.filename}')
            Helper.render(note.filename, format, run_biber[note])


        rerendered = []

        for link in new_links:
            if link.target.note in rerendered:
                continue
            print(f'Rendering {link.target.note.filename}')
            Helper.render(link.target.note.filename, format)
            rerendered.append(link.target.note)


        #rerender the originals if some other rendering has occured
        rerendered = []
        for link in new_links:
            if link.source in rerendered:
                continue
            print(f'rendering {link.source.filename}')
            Helper.render(link.source.filename, format)
            rerendered.append(link.source)


    def synchronize():
        """
            Reads all the files that have been changed since the last call of this function and updates the database
        """


        #loop through all the tracked notes and check for required updates
        to_read = []
        for note in database.Note:
            #try and get the edit date from the file system. 
            try:
                file = os.path.join('notes', 'slipbox', f'{note.filename}.tex')
                modified = os.path.getmtime(file)

                if datetime.datetime.fromtimestamp(modified) > note.last_edit_date:
                    to_read.append(note)
                    note.last_edit_date = datetime.datetime.fromtimestamp(modified)
                    note.save()

            except FileNotFoundError:
                #Todo: file has been deleted or renamed without the database being updated really need to run force_synchronize.
                print(f'file not found for note with reference {note.reference}')
                pass

        #update labels 
        run_biber = {}
        for note in to_read:
            Helper.__update_labels(note)
            run_biber[note] = Helper.__update_citations(note)


        new_links = []
        for note in to_read:
            new_links.extend(Helper.__update_links(note))


        return to_read, new_links, run_biber



    def force_synchronize():
        """
            Reads the file documents.tex and adds these files to the database (/slipbox.db) and checks for files in /notes that aren't in the documents. Then fixes and confilcts with these before reading the notes and creating database objects for labels, links and citations. 
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
            filepath = os.path.join('notes', 'slipbox', f'{filename}.tex')
            modified = datetime.datetime.fromtimestamp(os.path.getmtime(filepath))


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
            Helper.__update_labels(note)
            Helper.__update_citations(note)

        #add connections

        for note in database.Note: 
            Helper.__update_links(note)





    def list_unreferenced():
        from LatexZettel import analysis
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

        import subprocess
        if filename is None:
            most_recent = Helper.__get_recent_files(1)[0]
            os.chdir(os.path.join('notes','slipbox'))
            subprocess.call([OPEN_COMMAND, os.path.split(most_recent)[1]])
        else:
            os.chdir(os.path.join('notes','slipbox'))
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


    def export_project(project_folder, texfile=None):
        """

            Replaces \\transclude calls in a project file with the contents of the notes. Output is saved in project_dir/standalone

        """

        if texfile is None:
            texfile = f'{project_folder}.tex'

        output_dir = os.path.join('projects', project_folder, 'standalone')

        try:
            os.mkdir(output_dir)
        except FileExistsError:
            print('Export already exists, continue? (Warning: This will overwrite any changes you have made to the file {texfile} in {output_dir})')
            if not Helper.__getyesno():
                return



        output = bytearray()
        input_file = os.path.join('projects', project_folder, texfile)

        with open(input_file, 'r') as f:
            for line in f:

                output.extend((re.sub('\\\\transclude(\[[^]]+\]+)?\{([^}]+)\}', '', line).strip() + '\n').encode())
                external_documents = re.finditer('\\\\transclude(\[([^]]+)\])?\{([^}]+)\}', line)
                for document in external_documents:
                    tag = document.group(2)
                    document = document.group(3)
                    if tag is None:
                        tag = 'note'

                    note_file = os.path.join('notes', 'slipbox', f'{document}.tex')
                    with open(note_file, 'r') as in_file:
                        full_document = in_file.read() 
                        import_text = re.search(f'%<\*{tag}>((.|\n)*?)%</{tag}>', full_document)
                        output.extend(import_text.group(1).strip().encode())

        out_file = os.path.join(output_dir, texfile)

        with open(out_file, 'wb') as f:
            f.write(output)

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

    def remove_duplicate_citations():
        for note in database.Note:
            tracked = [c for c in note.citations]
            tracked_keys = [c.citationkey for c in tracked]

            tracked_set = set(tracked_keys)

            if len(tracked_set) < len(tracked_keys):
                print(f'deleting duplicate keys in {note.filename}')
                for key in tracked_set:
                    citation_instances =  [c for c in database.Citation.select().where(database.Citation.note == note, database.Citation.citationkey==key)]

                    for i, c in enumerate(citation_instances):
                        if i == 0:
                            continue

                        c.delete_instance()


    def __update_citations(note):
        keys = Helper.__getcitations(note)
        tracked = [c for c in note.citations]
        tracked_keys = [c.citationkey for c in tracked]



        updates_to_citations = False

        for key in keys:
            if key in tracked_keys:
                continue
            database.Citation.create(note=note, citationkey=key)
            updates_to_citations = True


        for citation in tracked:
            if citation.citationkey not in keys:
                citation.delete_instance()
                updates_to_citations = True

        return updates_to_citations



    def __update_labels(note):
        labels = Helper.__getlabels(note)
        tracked_labels = [label.label for label in note.labels]
        for label in labels:
            if label not in tracked_labels:
                database.Label.create(label=label, note=note)

            #remove extra labels
        for label in note.labels:
            if label.label not in labels:
                label.delete_instance()

        #add connections

    def __update_links(note):

        links = Helper.__getlinks(note)
        modified = []

        tracked = [(link.target.note.reference, link.target.label) for link in note.references] 
            #add in untracked
        for link in links:
            if link not in tracked:
                try:
                    label = database.Label.get(note__reference=link[0], label=link[1])
                    link = database.Link.create(target=label, source=note)
                    modified.append(link)
                except database.Label.DoesNotExist:
                    print(f'label in {note.filename} with details {link[0]}, {link[1]} does not exist')

        #remove any that no longer exist
        for link in note.references:
            if (link.target.note.reference, link.target.label) not in links:
                print(f'link {(link.target.note.reference, link.target.label)} no longer exists, deleting')
                link.delete_instance()
                modified.append(link)


        return modified 


    def __getnotefiles(directory='notes/slipbox'):
        notes = [str(f) for f in files.get_files(directory, '.tex')]
        return notes

    def __createnotefile(filename, extension = 'tex'):
        try:
            os.mkdir('notes')
        except FileExistsError:
            pass

        if extension == 'tex':
            folder = os.path.join('notes', 'slipbox')
        else:
            folder = os.path.join('notes', extension)


        try:
            os.mkdir(folder)
        except FileExistsError:
            pass


        try:
            with open(os.path.join(folder, f'{filename}.{extension}'), 'r') as f:
                pass
            print(f'File {folder}/{filename}.{extension} already exists, skipping copying the template')
            return
        except FileNotFoundError:
            pass


        file = bytearray()
        title = ' '.join([s.capitalize() for s in filename.split('_')])

        with open(os.path.join('template', f'note.{extension}'), 'r') as f:
            for i, line in enumerate(f):
                if extension == 'tex':
                    file.extend((re.sub('\\\\title\{(.*?)\}', '\\\\title{' + title + '}', line)).encode())
                elif extension == 'md':
                    file.extend((re.sub('Note Title', title, line)).encode())


        with open(os.path.join(folder, f'{filename}.{extension}'), 'wb') as f:
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


    def list_citations(filename):
        Helper.__getcitations(database.Note.get(filename=filename))

    def __getcitations(note):
        citation_commands = ['cite', 'parencite', 'footcite', 'footcitetext', 'textcite', 'smartcite', 'cite*', 'parencite*', 'supercite', 'autocite', 'autocite*', 'citeauthor', 'citeauthor*', 'citetitle', 'citeyear', 'citedate', 'citeurl', 'volcite', 'pvolcite', 'fvolcite', 'ftvolcite', 'svolcite', 'tvolcite', 'avolcite', 'fillcite', 'footfullcite', 'nocite', 'notecite', 'pnotecite', 'fnotecite']


        file_path = os.path.join('notes', 'slipbox', f'{note.filename}.tex')
        keys = set()
        with open(file_path, 'r') as f:
            for line in f:
                citations = re.finditer('\\\\(' + '|'.join(citation_commands) + ')(\[([^]]+)\])?(\{[^\}]+\})?(\[([^]]+)\])?\{([^\}]+)\}', line)
                for match in citations:
                    key = match.group(7)
                    keys.add(key)


        return keys

    def __getlinks(note):
        notes = Helper.__getnotefiles()
        file_references = []
        with open(f'notes/slipbox/{note.filename}.tex', 'r') as f:
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
