import peewee as pw


database = pw.SqliteDatabase('files.db')

class BaseModel(pw.Model):
    class Meta:
        database = database

class Note(BaseModel):
    filename = pw.CharField()  #filename of the note, eg note.tex or subfolder/note.tex
    reference = pw.CharField() #\externaldocument reference for the note, default value for example_note.tex would be ExampleNote.
    last_build_date = pw.DateTimeField()
    last_edit_date = pw.DateTimeField()


class Citation(BaseModel):
    """
        Model to keep track of which notes reference papers.
    """
    note = pw.ForeignKeyField(Note, on_delete='CASCADE', backref='citations')
    citationkey = pw.CharField()



class Link(BaseModel):
    """
        Model to keep track of links between files
    """
    source = pw.ForeignKeyField(Note, on_delete='CASCADE', backref='references') #note containing the reference
    target = pw.ForeignKeyField(Note, on_delete='CASCADE', backref='referenced_by') #note being referenced
    target_label = pw.CharField() #\excref{target}{target_label}

class Label(BaseModel):
    note = pw.ForeignKeyField(Note, on_delete='CASCADE', backref='labels')
    label = pw.CharField()

class Tag(BaseModel):
    name = pw.CharField()
    notes = pw.ManyToManyField(Note)

NoteTag = Tag.notes.get_through_model()

def create_tables(*models):
    with database:
        database.create_tables(models)

