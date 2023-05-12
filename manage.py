#!/bin/python3
import sys

import shutil
from LatexZettel import files, database, analysis
import re
import os
import peewee as pw
import datetime

class Helper:
    renderers = {'pdf': 'pdflatex', 'html': 'make4ht'}

    def help():
        print("""

            Manage the LaTeX slip box. This file should never be executed with the working directory not the base directory of the slipbox project.
        """)

    def addtodocuments(filename, reference=""):
        """
            Adds line \externaldocument[reference-]{filename} to documents.tex
            If reference is not supplied then it defaults to, for example, NoteName if filename=note_name
        """
            

        with open('notes/documents.tex', 'a') as f:
            f.write(f'\externaldocument[{reference}-]{{{filename}}}\n')



    def getnotefiles(directory='notes/slipbox'):
        notes = [str(f) for f in files.get_files(directory, '.tex')]
        return notes

    def createnotefile(filename):
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
        except FileNotFoundError:
            shutil.copyfile('template/note.tex', f'notes/slipbox/{filename}.tex')
            return

        print(f'File notes/{filename}.tex already exists, skipping copying the template')
    

    def newnote(note_name, reference_name=""):
        """
            createnote note_name [Optional ReferenceName]
            Creates note with name note_name.tex, Second argument is optional and is the name in the reference, defaults to NoteName

            to do: check whether a file already exists etc

        """
        if reference_name == "":
            reference_name = ''.join([w.capitalize() for w in note_name.split('_')])
        
        #see if the note already exists
        try:
            note = database.Note.get(filename=note_name)
            raise ValueError(f'A note with file name {filename} already exists in the database. If this is not the case then run manage.py synchronize to update the database, and then try again')
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
    
        Helper.createnotefile(note_name)
        Helper.addtodocuments(note_name, reference_name)
        #once created, add note to database 
        note = database.Note(filename=note_name, reference=reference_name, created_at = datetime.datetime.now(), modified_date = datetime.datetime.now())
        note.save()

    def removenote(filename):
        try:
            note = database.Note.get(filename=filename)
            print('Delete database entry? (y/n)') 
            if Helper.getyesno():
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
            if Helper.getyesno():
                lines.pop(i)
        
        with open('notes/documents.tex', 'w') as f:
            for line in lines:
                f.write(line)


        print(f'Delete notes/slipbox/{filename}.tex? (y/n)')
        if Helper.getyesno():
            try:
                os.remove(f'notes/slipbox/{filename}.tex')
            except FileNotFoundError:
                print('Error, no such file exists')

    

    def render(filename, format='pdf'):
        import subprocess
        command = Helper.renderers[format]
        
        try:
            os.mkdir(format)
        except FileExistsError:
            pass
        os.chdir(format)


        path_to_file = f'../notes/slipbox/{filename}.tex'


        try:
            with open(path_to_file, 'r'):
                pass
        except FileNotFoundError:
            print('No such file!')
            return '', f'Can\'t find {path_to_file}'


        process = subprocess.run([command, '--interaction=nonstopmode', path_to_file], capture_output=True)

        os.chdir('../')

        return process.stdout, process.stderr

        

    def renderall(format='pdf'):
        pass

        
    def biber(filename, folder='pdf'):
        import subprocess
        os.chdir(folder)
        process = subprocess.run(['biber', filename], capture_output=True)
        output, error = process.stdout, process.stderr
        os.chdir('../')

        return output, error
        

    def renderallhtml():
        """
            Renderes all the notes using make4ht. Saves output in /html
        """

        notes = Helper.getnotefiles()
        try:
            os.mkdir('html')
        except FileExistsError:
            pass
        os.chdir('html')

        for note in notes:
            filename = note[:-4] 
            os.system(f'make4ht -c ../config/make4ht.cfg ../{note} svg')
            os.system(f'biber {filename}')

        for note in notes:
            filename = note[:-4] 
            os.system(f'make4ht -c ..config/make4ht.cfg ../{note} svg')
       
       
    def renderallpdf():
        """
            Renderes all the notes using pdflatex. Saves output in /pdf
        """
        import subprocess
        
        notes = Helper.getnotefiles()
        

        print('render pass 1')
        for note in notes:
            filename = ''.join(note[:-4].split('notes/slipbox/')[1:])
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
            filename = ''.join(note[:-4].split('notes/slipbox/')[1:])
            print(f'rendering {filename}...', end='')
            output, error = Helper.render(filename)
            if error == '':
                print('done')
            else:
                print('\n',error)
                

    def getyesno():
        while True:
            a = input()
            if a == 'y':
                return True
            elif a == 'n':
                return False
            else:
                print('Please enter either \'y\' or \'n\'')

    def synchronize():
        """
            Reads the file documents.tex and adds these files to the database, then checks for files in /notes that aren't in the documents
        """
        database.create_all_tables()
        notes = Helper.getnotefiles()
        notes = [''.join(note.split('notes/slipbox/')[1:])[:-4] for note in notes]
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
                        if Helper.getyesno():
                            Helper.createnotefile(filename)
                            tracked_notes[filename] = reference_name
                            
                    else:
                        tracked_notes[filename] = reference_name

        for filename, reference_name in tracked_notes.items():
            modified = datetime.datetime.fromtimestamp(os.path.getmtime(f'notes/slipbox/{filename}.tex'))

            try:
                note = database.Note.get(filename=filename)
                note.last_edit_date = modified
                if note.reference == reference_name:
                    continue #nothing to do
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
                if Helper.getyesno(): 
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
                labels = Helper.getlabels(note)
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
                links = Helper.getlinks(note)
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


            



    def getlabels(note):
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




    def getlinks(note):
        notes = Helper.getnotefiles()
        file_references = []
        with open(f'notes/slipbox/{note.filename}.tex') as f:
            for line in f:
                links = re.finditer('\\\\ex(hyper)?(c)?ref\[(.*?)\]\{(.*?)\}', line)
                for link in links:
                    file_references.append((link.group(4), link.group(3))) 
        return file_references

    def gettags():
        notes = Helper.getnotefiles()
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


                        
    def listunreferenced():
        import numpy as np
        notes, adj_matrix = analysis.calculate_adjacency_matrix()

        referenced_by = np.sum(adj_matrix, axis=0)
        
        number = 1
        for note, links_from in zip(notes, referenced_by):
            if links_from == 0:
                print(f'{number}: {note.filename}')
                number += 1

    def plotgraph():
        import networkx as nx
        from pyvis.network import Network

        notes, adj = analysis.calculate_adjacency_matrix()

        graph = nx.DiGraph(adj)
        graph = nx.relabel_nodes(graph, {i: note.filename for i, note in enumerate(notes)})

        nt = Network('1080px', '1920px', directed=True)
        nt.toggle_physics(True)
        nt.from_nx(graph)


        nt.show('network.html', notebook=False)



def main(args):
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
