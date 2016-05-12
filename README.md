# OMP Modules

Python modules for web2py [OMP portal](https://github.com/UB-Heidelberg/UBHD-OMPPortal).

## ompdal

Contains 

* function wrappers for frequent database queries,
* basic classes for OMP items and settings.

### DB functions

In general, for every OMP item, there is a function `get<OMPItemName>(omp_item_id)` that returns a database row object, if the item with the specified id exists, `None` otherwise. Example:

```
def getSubmission(self, submission_id):
  return self.db.submissions[submission_id]
```

In addition, there can be functions of the form `get<OMPItemName>By<Parameter>(parameter)`, for example:

```
def getSubmissionsByPress(self, press_id, ignored_submission_id=-1, status=3):
  s = self.db.submissions
  q = ((s.context_id == press_id)
    & (s.submission_id != ignored_submission_id)
    & (s.status == status)
  )
  return self.db(q).select(s.ALL, orderby=~s.date_submitted)
```

OMP items usually feature a settings table with (optional) localized settings. These are returned by functions of the form `get<OMPItemName>Settings(omp_item_id)`. Example:

```
def getSubmissionSettings(self, submission_id):
  q = (self.db.submission_settings.submission_id == submission_id)
  return self.db(q).select(self.db.submission_settings.ALL)
```

There are further, more specific functions for several items. See module docstrings for details.

### OMP classes

The module features two basic classes, ```OMPItem``` and ```OMPSettings```. ```OMPItem``` can be used to wrap any OMP object, such as submissions, authors, publication formats etc. that are accompagnied by settings. Settings can be wrapped with an ```OMPSettings``` class for handling localization. Both classes only have getter methods, since the web2py OMP portal only reads the database. Associations between items (e.g. editors associated with a series) can be modeled via the optional ```associated_items``` dictionary in ```OMPItem```.

## ompformat

Contains formatting helper functions for 

* citations,
* download links, 
* publication dates,
* ...

See docstrings for details.
