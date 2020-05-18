# How to create a Kanban (Trello style) view of your ModelAdmin data in Wagtail

Goal: Create a ModelAdmin mixin that will make it easy to show an index view as a kanban board.

Why: Visual control is very helpful for planning and also a high level understanding of information. Kanban boards provide a recognisable way to show sets of items in columns that represent their 'status' or grouping.

How: We want this to be as simple as possible, leveraging existing ModelAdmin conventions where possible and keeping as much of the logic being on the server. Drag & drop would be great but happy to sacrifice real time / async Javascript behaviour to gain simplicity.

Inspiration: kanban, notion.so, Trello, Github & Gitlab kanban interface.

## Getting Started

Vesions

- Wagtail 2.9 / 2.10
- Python 3.6
- Django 3.0.5
- jkanban 1.2 (Javascript/npm library)

Key Parts to Understand

- Terminology
- ModelAdmin (Wagtail's not Django's)
- Class Mixin

## Tutoral

### 1. Prepare a ModelAdmin model

For this tutorial we will be using [ArsTechnica](https://arstechnica.com)'s [Rocket Report](https://arstechnica.com/newsletters/?subscribe=248910) as inspiration. As of writing the latest report was [Rocket Report: Branson sells Virgin Galactic shares, LEGO’s deep-space rocket](https://arstechnica.com/science/2020/05/rocket-report-busy-weekend-on-the-space-coast-sls-rocket-launch-slips/).

This regular post contains a `title`, `byline`, `preamble`, a `reports` section which breaks up the news snippets into class of launch (small, medium and large). At the end of the report there is a small `timeline` of upcoming launches. The part we want to focus on for this tutorial is the `reports` section, and [Wagtail's snippets](https://docs.wagtail.io/en/stable/topics/snippets.html) are a perfect way to store this kind of related content in a centralised way.

#### Create app

We assume you already have a Wagtail application up and running, so our first step will be to find a place to store all our custom logic and models. We will [start a new app](https://docs.djangoproject.com/en/3.0/ref/django-admin/#startapp) called `rocket_report`.

1. Run `django-admin startapp rocket_report`
2. Update your `settings.py`

```python
INSTALLED_APPS = [
  # ...
  'rocket_report',
  # ... wagtail & django items
]
```

There will now be an app folder `rocket_report` with models, views, etc.

#### Create page Model

Our next step will be to define our `RocketReportPage` [page model](https://docs.wagtail.io/en/stable/topics/pages.html).

1. Add a page model to your `models.py` file, code example below.
2. Run `./manage.py makemigrations` & `./manage.py migrate`
3. Restart the dev server to validate that we can now add a Rocket Report Page in Wagtail's admin
4. Add one page for use throughout the rest of the tutorial

```python
from django.db import models

from modelcluster.fields import ParentalKey

from wagtail.core.models import Page, Orderable
from wagtail.core.fields import RichTextField
from wagtail.admin.edit_handlers import FieldPanel, InlinePanel
from wagtail.images.edit_handlers import ImageChooserPanel


class RocketReportPage(Page):

    # Database fields
    byline = models.CharField(blank=True, max_length=120)
    preamble = RichTextField(blank=True)
    main_image = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    # Editor panels configuration
    content_panels = Page.content_panels + [
        FieldPanel("byline"),
        FieldPanel("preamble", classname="full"),
        ImageChooserPanel("main_image"),
        # TBC - reports
        InlinePanel("related_launches", label="Timeline"),
    ]


class Launch(Orderable):
    page = ParentalKey(
        RocketReportPage, on_delete=models.CASCADE, related_name="related_launches"
    )
    date = models.DateField("Launch date")
    details = models.CharField(max_length=255)

    panels = [
        FieldPanel("date"),
        FieldPanel("details"),
    ]
```

#### Create snippet Model

Our rocket report items will be [Wagtail Snippets](https://docs.wagtail.io/en/stable/topics/snippets.html), this gives a simple way to edit, manage and select these items for our pages.

1. Add the snippet model to your same `models.py` file, code example below.
2. Run `./manage.py makemigrations` & `./manage.py migrate`
3. Restart the dev server to validate that we can now add the snippet in Wagtail's admin
4. Add some snippet entries for use throughout the rest of the tutorial

```python
from django.db import models
# ... include existing imports from model.py
from wagtail.snippets.models import register_snippet
from wagtail.snippets.edit_handlers import SnippetChooserPanel
from wagtail.admin.edit_handlers import FieldPanel


class RocketReportPage(Page):
    # ...
    content_panels = Page.content_panels + [
        # ... other field panels
        ImageChooserPanel("main_image"),
        # ... other field panels
    ]


@register_snippet
class RocketReport(models.Model):

    STATUS_CHOICES = [
        ("SUBMITTED", "Submitted"),
        ("REVIEWED", "Reviewed"),
        ("PROPOSED", "Proposed"),
        ("HOLD", "Hold"),
        ("CURRENT", "Current"),
    ]

    CATEGORY_CHOICES = [
        ("BLANK", "Uncategorised"),
        ("SMALL", "Small"),
        ("MEDIUM", "Medium"),
        ("LARGE", "Large"),
    ]

    submitted_url = models.URLField(null=True, blank=True)
    submitted_by = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=255, blank=True, choices=STATUS_CHOICES)
    title = models.CharField(max_length=255)
    content = RichTextField(blank=True)
    category = models.CharField(
        max_length=255, choices=CATEGORY_CHOICES, default="BLANK"
    )

    panels = [
        FieldPanel("title"),
        FieldPanel("status"),
        FieldPanel("category"),
        FieldPanel("content"),
        FieldPanel("submitted_url"),
        FieldPanel("submitted_by"),
    ]

    def __str__(self):
        return self.title


class RocketReportPageReportPlacement(Orderable, models.Model):
    page = ParentalKey(
        RocketReportPage, on_delete=models.CASCADE, related_name="rocket_reports"
    )
    rocket_report = models.ForeignKey(
        RocketReport, on_delete=models.CASCADE, related_name="+"
    )

    panels = [
        SnippetChooserPanel("rocket_report"),
    ]

    def __str__(self):
        return self.page.title + " -> " + self.rocket_report.title

```

#### Register with ModelAdmin

Now we can register the report model using [`ModelAdmin`](https://docs.wagtail.io/en/stable/reference/contrib/modeladmin/index.html). Note that this is Wagtail's ModelAdmin not Django's.

1. Add `wagtail.contrib.modeladmin` to your `INSTALLED_APPS` in your `settings.py`
2. Add a new `ModelAdmin` class in admin.py, code example below.
3. Register this class in a new file `wagtail_hooks.py`, code example below.
4. Validate that we now have an admin sidebar item for 'Rocket Reports' which will show the default ModelAdmin item list.

```python
# admin.py
from wagtail.contrib.modeladmin.options import ModelAdmin

from .models import RocketReport


class RocketReportAdmin(ModelAdmin):
    model = RocketReport
    menu_icon = "fa-rocket"
    list_display = ("title", "status", "category", "submitted_by")
    list_filter = ("status", "category")
    search_fields = ("title", "status", "category", "submitted_by")

```

```python
# wagtail_hooks.py
from wagtail.contrib.modeladmin.options import modeladmin_register

from .admin import RocketReportAdmin

modeladmin_register(RocketReportAdmin)

```

### 2. Create a template, view & mixin

We are going to now set up a custom `KanbanMixin` that will house the customisations to our `ModelAdmin`. We could put all of these customisations directly on our `RocketReportAdmin` but we want to set up something reusable. It would be good to have a basic understanding of how to [customise the index view (listing)](https://docs.wagtail.io/en/stable/reference/contrib/modeladmin/indexview.html) before reading on.

#### Create kanban index template

We will be using a Javascript library do the client side rendering and handling of interaction for our basic Kanban board. There are a lot of [Kanban JS libraries on Github](https://github.com/topics/kanban?l=javascript) and a few [Kanban packages on NPM](Kanban packages on NPM).

The package we will use is [Jkanban](https://www.riccardotartaglia.it/jkanban/), it has a simple API and does not rely on third party dependencies. For simplicity we will use the jsdelivr service to provide our script and css, find the package and use the [dist directory to get your script and style tags](https://www.jsdelivr.com/package/npm/jkanban?path=dist).

1. Create a template file `/templates/modeladmin/kanban_index.html`
2. To inherit the existing modeladmin index listing layout (header, search bar, title etc) add `{% extends "modeladmin/index.html" %}` at the top
3. The content blocks we will use, provided by the above template are `extra_css`, `extra_js` and `content_main`.
4. Remember to add `{{ block.super }}` to the js & css blocks so that existing scripts and styles will be used.
5. `content_main` block - add a div that will contain the kanban with class `kanban-wrapper listing` and an inner div with an id `kanban-mount` which is used by JKanban to add the rendered kanban board
6. `extra_css` block - Add the `link` tag from jsdelivr and some basic styles within a `<style>` tag, in the code below we are starting with some margins and handling of longer boards
7. `extra_js` block - our goal is to simply load up some dummy data based on the [options docs for jKanban](https://github.com/riktar/jkanban#var-kanban--new-jkanbanoptions)

```javascript
document.addEventListener("DOMContentLoaded", function () {
  var options = {
    boards: [
      {
        id: "column-0",
        title: "Column A",
        item: [
          { id: "item-1", title: "Item 1" },
          { id: "item-2", title: "Item 2" },
          { id: "item-1", title: "Item 3" },
        ],
      },
      {
        id: "column-1",
        title: "Column B",
        item: [
          { id: "item-4", title: "Item 4" },
          { id: "item-5", title: "Item 4" },
          { id: "item-5", title: "Item 6" },
        ],
      },
    ],
  };

  // build the kanban board with supplied options
  var kanban = new jKanban(
    Object.assign({}, options, { element: "#kanban-mount" })
  );
});
```

##### Full template code

```html
{% extends "modeladmin/index.html" %}
{% comment %} templates/modeladmin/kanban_index.html {% endcomment %}

{% block extra_css %}
    {{ block.super }}
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/jkanban@1.2.1/dist/jkanban.min.css" integrity="sha256-0qQUTR+++z/x9FrRZQGS5mM6wQCGulXRHHej0Izs5Uk=" crossorigin="anonymous">
    <style>
      .kanban-wrapper {
        width: 100%;
        overflow-x: auto; /* add horizontal scrolling for wide boards */
        margin-top: 1rem;
        margin-bottom: 1rem;
      }

      .kanban-item {
        min-height: 4rem;
      }
    </style>
{% endblock %}

{% block extra_js %}
  {{ block.super }}
  <script src="https://cdn.jsdelivr.net/npm/jkanban@1.2.1/dist/jkanban.min.js" integrity="sha256-prhXO+8mpwVwh95I3O5X4O1enmfl0pqRp7Kc7XKYHRs=" crossorigin="anonymous"></script>
  <script>
    document.addEventListener('DOMContentLoaded', function() {
      var options = {
        boards: [
          {
            id: 'column-0',
            title: 'Column A',
            item: [{ id: 'item-1', title: 'Item 1'}, { id: 'item-2', title: 'Item 2'}, { id: 'item-1', title: 'Item 3'}]}
          ,
          {
            id: 'column-1',
            title: 'Column B',
            item: [{ id: 'item-4', title: 'Item 4'}, { id: 'item-5', title: 'Item 4'}, { id: 'item-5', title: 'Item 6'}]
          }
        ]
      };

      // build the kanban board with supplied options
      // see: https://github.com/riktar/jkanban#var-kanban--new-jkanbanoptions
      var kanban = new jKanban(Object.assign({}, options, {element: '#kanban-mount'}));
    });
  </script>
{% endblock %}

{% block content_main %}
  <div class="kanban-wrapper listing">
    <div id="kanban-mount"></div>
  </div>
{% endblock %}
```

#### Create Mixin with template override

A template is only good if we can get our `ModelAdmin` to use it when rendering the index listing view instead of the default. We can leverage a mixin approach to override the `ModelAdmin` methods while still honouring the [existing config on a per app or model basis](https://docs.wagtail.io/en/stable/reference/contrib/modeladmin/primer.html#overriding-templates).

1. We will store our mixin in the `admin.py` file.
2. `ModelAdmin` uses a method `get_index_template` to get the index listing template, simply override this to call the defined `index_template_name` or `get_templates("kanban_index")`.
3. This will ensure that the template made above will be found at `templates/modeladmin/kanban_index.html`
4. Be sure to add the mixin to your `RocketReportAdmin` class, before the `ModelAdmin` usage.

```python
# rocket_report/admin.py

class KanbanMixin:
    def get_index_template(self):
        # leverage the get_template to allow individual override on a per model basis
        return self.index_template_name or self.get_templates("kanban_index")


class RocketReportAdmin(KanbanMixin, ModelAdmin):
    model = RocketReport
    # ...
```

#### Create View to supply mock data to the kanban board

Our goal is to keep as much logic on the server, so we need a way to provide the board data from our Django view to our client. Doing this comes with some issues of encoding/decoding and ensuring that server generated content cannot inject Javascript.

Thankfully, Django helps us out with its builtin tag [`json_script`](https://docs.djangoproject.com/en/3.0/ref/templates/builtins/#json-script) which provides a way for sever generted content to be provided to JS in a view in a safe way.

1. Add a new view to the app's `views.py` called `KanbanView`
2. This view will inhert the modeladmin `wagtail.contrib.modeladmin.views.IndexView`
3. Override `get_context_data`, calling super and then adding `kanban_options` with simular dummy data that we used in the template

```python
# views.py
from wagtail.contrib.modeladmin.views import IndexView


class KanbanView(IndexView):
    def get_kanban_data(self, context):
        return [
            {
                "id": "column-id-%s" % index,
                "item": [
                    {"id": "item-id-%s" % obj["pk"], "title": obj["title"],}
                    for index, obj in enumerate(
                        [
                            {"pk": index + 1, "title": "%s Item 1" % column},
                            {"pk": index + 2, "title": "%s Item 2" % column},
                            {"pk": index + 3, "title": "%s Item 3" % column},
                        ]
                    )
                ],
                "title": column,
            }
            for index, column in enumerate(["column a", "column b", "column c"])
        ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # see: https://github.com/riktar/jkanban#var-kanban--new-jkanbanoptions
        context["kanban_options"] = {
            "addItemButton": False,
            "boards": self.get_kanban_data(context),
            "dragBoards": False,
            "dragItems": False,
        }

        return context
```

#### 


#### Read the server provided options in the template

- load kanban board with fake data here

### 3. Render all items in one column

### 4. Render columns

### 5. Render columns with correct items

### 6. Add drag & drop handling

## Final Solution

- Code can be found at ...
- Screenshots & gif

## Future Improvements

- Better handling of preseting 'values' for each item's field/value, currently renders inside `<td>` tags due to existing `ModelAdmin` assumptions
- Real time drag & drop, column number updates, including toast style messages for updates
- This implementation requires that the column be based on a field in the model, handling of `ModelAdmin`'s custom methods for column name would be great.
- Handling re-ordering within columns
- Auto or configurable colouring of column headers
