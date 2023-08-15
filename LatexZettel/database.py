import peewee as pw


database = pw.SqliteDatabase('slipbox.db', pragmas={'foreign_keys': 1})

class BaseModel(pw.Model):
    class Meta:
        database = database

class Note(BaseModel):
    filename = pw.CharField(unique=True)  #filename of the note, eg note.tex or subfolder/note.tex
    reference = pw.CharField(unique=True) #\externaldocument reference for the note, default value for example_note.tex would be ExampleNote.
    last_build_date_html = pw.DateTimeField(null=True)
    last_build_date_pdf = pw.DateTimeField(null=True)
    last_edit_date = pw.DateTimeField(null=True)
    created = pw.DateTimeField(null=True)


class Citation(BaseModel):
    """
        Model to keep track of which notes reference papers.
    """
    note = pw.ForeignKeyField(Note, on_delete='CASCADE', backref='citations')
    citationkey = pw.CharField()


class Label(BaseModel):
    note = pw.ForeignKeyField(Note, on_delete='CASCADE', backref='labels')
    label = pw.CharField()


class Link(BaseModel):
    """
        Model to keep track of links between files
    """
    source = pw.ForeignKeyField(Note, on_delete='CASCADE', backref='references') #note containing the reference
    target = pw.ForeignKeyField(Label, on_delete='CASCADE', backref='referenced_by') #\excref{target}{target_label}


class Tag(BaseModel):
    name = pw.CharField(unique=True)
    notes = pw.ManyToManyField(Note)

NoteTag = Tag.notes.get_through_model()

def create_tables(*models):
    with database:
        database.create_tables(models)

def create_all_tables():
    create_tables(Note, Citation, Link, Label, Tag)

