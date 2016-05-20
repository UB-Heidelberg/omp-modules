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

## OMP Stats
 * is a  web2py module,  reads a json output  and converts into a  dynamic HTML Table
 * any api service returning jsons in the following format is supported.  For a reference implementation please check [API](http://heiup.uni-heidelberg.de/cgi-bin/oastats-json.cgi?repo=omphp&type=json&ids=43-231-xml,43-230-pdf)

```
{
  "43-231-xml": {
    "all_years": [
      {
        "volltext": "515",
        "id": "43-231-xml",
        "zeitraum": "16",
        "frontdoor": "0"
      },
      {
        "volltext": "507",
        "id": "43-231-xml",
        "frontdoor": "0",
        "zeitraum": "15"
      }
    ]
  }
}
```

### Installation
  * add the following lines to you appconfig.ini, if not already defined. The id configuration is only necessary if you use the ub heidelberg api service, otherwise, please define your own relative script path. If you want to use a absolute path please change self.oas_server in the ompstats.py
 
```
[statistik]
id=omphp
script=cgi-bin/oastats-json.cgi
```
 * Add the follwing HTML snippet into the your view.
```

  {{if stats.checkOASService():}}
    {{file_types= ['xml','pdf']}}
    <div id="oas-widget" class="applied-to-ojs">
     <div class="btn btn-default" id="statistik-button">{{=T('Statistik since 07.03.16')}}</div> <br/>
     <div style="display:none" class="table" id="oas">
       <ul class="nav nav-tabs">
         <li class="active"><a href="#full" data-toggle="tab"><i class="icon-briefcase"></i> {{=T('Book')}}</a></li>
         <li class=""><a href="#chapters" data-toggle="tab">{{=T('Chapters')}}</a></li>
       </ul>
       <div class="tab-content">
         <div class="tab-pane active" id="full">
           <table class="table">
             {{=stats.getFullHTMLTable(submission_id,file_types)}}
           </table>
         </div>
         <div class="tab-pane" id="chapters">
           <table class="table">  {{=stats.getChapterHTMLTable(submission_id, file_types) }}</table>
         </div>
       </div>
     </div>
    </div>
    <script type="text/javascript">
    $('#statistik-button').click(function(){
    $('#oas').slideToggle()
    });
    </script>
{{pass}}

```





