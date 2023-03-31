import peewee as pw


database = pw.SqliteDatabase('files.db')

class BaseModel(pw.Model):
    class Meta:
        database = database

class Note(BaseModel):
    filename = pw.CharField(max_length=200)  #filename of the note, eg note.tex or subfolder/note.tex
    reference = pw.CharField(max_length=200) #\externaldocument reference for the note
    last_build_date = pw.DateTimeField()
    last_edit_date = pw.DateTimeField()


class Reference(BaseModel):
    """
        Model to keep track of which notes reference papers.
    """
    note = pw.ForeignKeyField(Note, on_delete='CASCADE')
    citationkey = pw.CharField(max_length=200)

class Link(BaseModel):
    """
        Model to keep track of links between files
    """
    source = pw.ForeignKeyField(Note, on_delete='CASCADE') #note containing the reference
    target = pw.ForeignKeyField(Note, on_delete='CASCADE') #note being referenced
    target_label = pw.CharField(max_length=200) #\excref{target}{target_label}

def create_tables(*models):
    with database:
        database.create_tables(models)

