# Copyright (C) 2007 Alexandre Conrad, aconrad(dot.)tlv(at@)magic(dot.)fr
#
# This module is part of FormAlchemy and is released under
# the MIT License: http://www.opensource.org/licenses/mit-license.php

import webhelpers as h
#from sqlalchemy.types import Binary, Boolean, Date, DateTime, Integer, NullType, Numeric, String, Time
from sqlalchemy.types import Binary, Boolean, Date, DateTime, Integer, Numeric, String, Time

__all__ = ["FieldSet", "MakeField", "Label", "Field", "TextField",
    "PasswordField", "HiddenField", "BooleanField", "FileField",
    "IntegerField", "DateTimeField", "DateField", "TimeField",
    "SelectField", "DropDownField"]
__version__ = "0.1"

# FIXME
# implement MakeField
# better NullType detection

INDENTATION = "  "

def wrap(start, text, end):
    return "\n".join([start, indent(text), end])

def indent(text):
    return "\n".join([INDENTATION + line for line in text.splitlines()])

class FormAlchemyOptions(dict):
    """The `FormAlchemyOptions` class.

    This is the class responsible for parsing and holding FormAlchemy options.
    It has the same API as `dict`.

    """

    def parse(self, model):
        """Parse options from `model`'s FormAlchemy subclass if defined."""
        if hasattr(model, "FormAlchemy"):
            [self.__setitem__(k, v) for k, v in model.FormAlchemy.__dict__.items() if not k.startswith('_')]

    def configure(self, **options):
        """Configure FormAlchemy's default behaviour.

        This will update FormAlchemy's default behaviour with the given
        keyword options. Any other previously set options will be kept intact.

        """

        self.update(options)

    def reconfigure(self, **options):
        """Reconfigure `FormAlchemyOptions` from scratch.

        This will clear any previously set option and update FormAlchemy's
        default behaviour with the given keyword options.

        """

        self.clear()
        self.configure(**options)

class Model(object):
    """The `Model` class.

    Takes a model as argument and provides convenient model methods.

    Methods:
      get_colnames(self, **kwargs)
      get_readonlys(self, **kwargs)
      get_coltypes(self)

    """

    def __init__(self, model):
        self.model = model
        self.col_names = self.get_colnames()
        self.col_types = self.get_coltypes()
        self.pk_cols = self.get_pks()
        self.fk_cols = self.get_fks()

    def get_colnames(self, **kwargs):
        """Return a list of filtered column names.

        Keyword arguments:
        * `pk=True` - Won't return primary key columns if set to `False`.
        * `fk=True` - Won't return foreign key columns if set to `False`.
        * `exclude=[]` - An iterable containing column names to exclude.

        """

        if kwargs:
            return self._get_filtered_cols(**kwargs)
        return self.model.c.keys()

    def _get_filtered_cols(self, **kwargs):
        pk = kwargs.get("pk", True)
        fk = kwargs.get("fk", True)
        exclude = kwargs.get("exclude", [])
        if not pk:
            exclude += self.pk_cols
        if not fk:
            exclude += self.fk_cols

        columns = []

        for col in self.col_names:
            if not col in exclude:
                columns.append(col)

        return columns

    def get_readonlys(self, **kwargs):
        """Return a list of columns that should be readonly.

        Keywords arguments:
        * `readonly_pk=False` - Will prohibit changes to primary key columns if set to `True`.
        * `readonly_fk=False` - Will prohibit changes to foreign key columns if set to `True`.
        * `readonly=[]` - An iterable containing column names to set as readonly.

        """

        ro_pks = kwargs.get("readonly_pk", False)
        ro_fks = kwargs.get("readonly_fk", False)
        readonlys = kwargs.get("readonly", [])

        if ro_pks:
            readonlys += self.pk_cols
        if ro_fks:
            readonlys += self.fk_cols

        columns = []

        for col in self.col_names:
            if col in readonlys:
                columns.append(col)

        return columns

    def get_coltypes(self):
        """Categorize columns by type.

        Return a nine key dict. Each key is a direct subclass of TypeEngine:
          * `Binary=[]` - a list of Binary column names.
          * `Boolean=[]` - a list of Boolean column names.
          * `Date=[]` - a list of Date column names.
          * `DateTime=[]` - a list of DateTime column names.
          * `Integer=[]` - a list of Integer column names.
          * `NullType=[]` - a list of NullType column names. # NOT AVAILABLE RIGHT NOW
          * `Numeric=[]` - a list of Numeric column names.
          * `String=[]` - a list of String column names.
          * `Time=[]` - a list of Time column names.

        """

        # FIXME: Is this the good way to handle field generation?
        # What shall we do about non-standard SQLAlchemy types that were
        # built directly off of a TypeEngine?
        # Although, this should handle custum types built from one of those.

#        col_types = dict.fromkeys([t for t in [Binary, Boolean, Date, DateTime, Integer, NullType, Numeric, String, Time]], [])
        col_types = dict.fromkeys([t for t in [Binary, Boolean, Date, DateTime, Integer, Numeric, String, Time]], [])

        for t in col_types:
            col_types[t] = [col.name for col in self.model.c if isinstance(col.type, t)]

        return col_types

    def get_by_type(self, string):
        """Return a list of `string` type column names.

        `string` is case insensitive.

        Valid `string` values:
          * "binary"
          * "boolean"
          * "date"
          * "datetime"
          * "integer"
          * "nulltype" # NOT AVAILABLE RIGHT NOW
          * "numeric"
          * "string"
          * "time"

        """

        keys = {
            "binary":Binary,
            "boolean":Boolean,
            "date":Date,
            "datetime":DateTime,
            "integer":Integer,
#            "nulltype":NullType,
            "numeric":Numeric,
            "string":String,
            "time":Time,
        }

        return self.col_types.get(keys[string.lower()], [])

    def get_unnullables(self):
        """Return a list of non-nullable column names."""
        return [col for col in self.model.c.keys() if not self.model.c[col].nullable]

    def get_pks(self):
        """Return a list of primary key column names."""
        return [col for col in self.model.c.keys() if self.model.c[col].primary_key]

    def get_fks(self):
        """Return a list of foreign key column names."""
        return [col for col in self.model.c.keys() if self.model.c[col].foreign_key]

class ModelRenderer(Model):
    """Return generated HTML fields from a SQLAlchemy mapped class."""

    def __init__(self, model):
        super(ModelRenderer, self).__init__(model)

    def render(self, **options):
        """Return HTML fields generated from the `model`.

        Keywords arguments:
        * `password=[]` - An iterable of column names that should be set as password fields.
        * `hidden=[]` - An iterable of column names that should be set as hidden fields.
        * `dropdown={}` - A dict holding column names as keys, dicts as values. These dicts have at least a `opts` key used for options. `opts` holds either:
            - an iterable of option names: `["small", "medium", "large"]`. Options will have the same name and value.
            - an iterable of paired option name/value: `[("small", "$0.99"), ("medium", "$1.29"), ("large", "$1.59")]`.
            - a dict where dict keys are option names and dict values are option values: `{"small":"$0.99", "medium":"$1.29", "large":"$1.59"}`.
            The `selected` key can also be set:
            `selected=value`: a string or a container of strings (when multiple values are selected) that will set the "selected" HTML tag to matching value options. It defaults to the SQLAlchemy mapped class's current value (if not None) or column default.
            Other keys can be given to be passed as standard HTML attributes, like multiple=<bool>, size=<integer> and so on.

{"meal":
    {"opts":[("Hamburger", "HB"),
             ("Cheeseburger", "CB"),
             ("Bacon Burger", "BB"),
             ("Roquefort Burger", "RB"),
             ("Pasta Burger", "PB"),
             ("Veggie Burger", "VB")],
     "selected":["CB", "BB"],    ## Or just "CB"
     "multiple":True,
     "size":3,
    }
}

        * `radio={}` - A dict holding column names as keys and an iterable as values. The iterable can hold:
          - input names: `["small", "medium", "large"]`. Inputs will have the same name and value.
          - paired name/value: `[("small", "$0.99"), ("medium", "$1.29"), ("large", "$1.59")]`.
          - a dict where dict keys are input names and dict values are input values: `{"small":"$0.99", "medium":"$1.29", "large":"$1.59"}`.

        * `prettify` - A function through which all label names will go. Defaults to: `"my_label".replace("_", " ").capitalize()`
        * `alias={}` - A dict holding the field name as the key and the alias name as the value. Note that aliases are beeing `prettify`ed as well.
        * `error={}` - A dict holding the field name as the key and the error message as the value.
        * `doc={}` - A dict holding the field name as the key and the help message as the value.
        * `cls_req="field_req"` - Sets the HTML class for fields that are not nullable (required).
        * `cls_opt="field_opt"` - Sets the HTML class for fields that are nullable (optional).
        * `cls_err=field_err` - Sets the HTML class for error messages.
        * `cls_doc="field_doc"` - Sets the HTML class for help messages.

        It also takes the same keywords as `get_readonlys`.

        """

        # Categorize columns
        columns = self.get_colnames(**options)
        readonlys = self.get_readonlys(**options)
        unnullables = self.get_unnullables()

        passwords = options.get('password', [])
        hiddens = options.get('hidden', [])
        dropdowns = options.get('dropdown', {})
        radios = options.get('radio', {})

        pretty_func = options.get('prettify')
        aliases = options.get('alias', {})

        errors = options.get('error', {})
        docs = options.get('doc', {})

        # Setup HTML classes
#        class_label = options.get('cls_lab', 'form_label')
        class_required = options.get('cls_req', 'field_req')
        class_optional = options.get('cls_opt', 'field_opt')
        class_error = options.get('cls_err', 'field_err')
        class_doc = options.get('cls_doc', 'field_doc')

        html = []

        # Generate fields.
        for col in columns:

            # Process hidden fields first as they don't need a `Label`.
            if col in hiddens:
                html.append(str(HiddenField(self.model, col)))
                continue

            # Make the label
            label = Label(self.model, col, alias=aliases.get(col, col))
            if callable(pretty_func):
                label.prettify = pretty_func # Apply staticmethod(pretty_func) ?
            if col in unnullables:
                label.cls = class_required
            else:
                label.cls = class_optional
            field = str(label)

            # Make the input
            if col in radios:
                radio = RadioSet(self.model, col, choices=radios[col])
                field += "\n" + str(radio)

            elif col in dropdowns:
                dropdown = DropDownField(self.model, col, dropdowns[col].pop("opts"), **dropdowns[col])
                field += "\n" + str(dropdown)

            elif col in passwords:
                field += "\n" + str(PasswordField(self.model, col, readonly=col in readonlys))

            elif col in self.col_types[String]:
                field += "\n" + str(TextField(self.model, col))

            elif col in self.col_types[Integer]:
                field += "\n" + str(IntegerField(self.model, col))

            elif col in self.col_types[Boolean]:
                field += "\n" + str(BooleanField(self.model, col))

            elif col in self.col_types[DateTime]:
                field += "\n" + str(DateTimeField(self.model, col))

            elif col in self.col_types[Date]:
                field += "\n" + str(DateField(self.model, col))

            elif col in self.col_types[Time]:
                field += "\n" + str(TimeField(self.model, col))

            elif col in self.col_types[Binary]:
                field += "\n" + str(FileField(self.model, col))

            else:
                field += "\n" + str(Field(self.model, col))

            # Make the error
            if col in errors:
                field += "\n" + h.content_tag("span", content=errors[col], class_=class_error)
            # Make the documentation
            if col in docs:
                field += "\n" + h.content_tag("span", content=docs[col], class_=class_doc)

            # Wrap the whole thing into a div
            field = wrap("<div>", field, "</div>")

            html.append(field)

        return "\n".join(html)

class FieldSet(Model):
    """The `FieldSet` class.

    This is the class responsible for generating HTML form fields. It needs
    to be instantiate with a SQLAlchemy mapped class as argument. The
    SQLAlchemy mapped class is held as `model`.

    The one method to use is `render`. This is the method that returns
    generated HTML code from the `model` object.

    FormAlchemy has some default behaviour set. It is configured to generate
    the most HTML possible that will reflect the `model` object. Although,
    you can configure FormAlchemy to behave differently, thus altering the
    generated HTML output by many ways:

      * By passing keyword options to the `render` method:

        render(pk=False, fk=False, exclude=["private_column"])

      These options are NOT persistant. You'll need to pass these options
      everytime you call `render` or FormAlchemy will fallback to it's
      default behaviour. Passing keyword options is usually meant to alter
      the HTML output on the fly.

      * At the SQLAlchemy mapped class level, by creating a `FormAlchemy`
      subclass, it is possible to setup attributes which names and values
      correspond to the keyword options passed to `render`:

        class MyClass(object):
            class FormAlchemy:
                pk = False
                fk = False
                exclude = ["private_column"]

      These attributes are persistant and will be used as FormAlchemy's
      default behaviour.

      * By passing the keyword options to FormAlchemy's `configure` method.
      These options are persistant. and will be used as FormAlchemy's default
      behaviour.

        configure(pk=False, fk=False, exclude=["private_column"])

    Note: In any case, options set at the SQLAlchemy mapped class level or
    via the `configure` method will be overridden if these same keyword
    options are passed to `render`.

    """

    def __init__(self, model):
        """Construct the `FieldSet` class.

        Arguments are:

          `model`
            An SQLAlchemy mapped class. This is the reference class.

        """

        super(FieldSet, self).__init__(model)

        # Attach a FormAlchemyOptions class to handle model's options.
        self._options = FormAlchemyOptions()
        self._options.parse(self.model)

        self.configure = self._options.configure
        self.reconfigure = self._options.reconfigure

    def render(self, **options):
        # Merge class level options with given argument options.
        opts = FormAlchemyOptions(self._options.copy())
        opts.configure(**options)

        html = ModelRenderer(self.model).render(**opts)

        legend = opts.pop('legend', None)
        # Setup class's name as default.
        if legend is None:
            legend_txt = self.model.__class__.__name__
        # Don't render a legend field.
        elif legend is False:
            return wrap("<fieldset>", html, "</fieldset>")
        # Use the user given string as the legend.
        elif isinstance(legend, basestring):
            legend_txt = legend

        html = h.content_tag('legend', legend_txt) + "\n" + html
        return wrap("<fieldset>", html, "</fieldset>")

class MakeField(object):
    """The `MakeField` class.

    The `MakeField` class is responsible for generating the appropriate HTML
    code given a `xField` object.

    The generated HTML returned contains <label> and <input> tag pairs.

    """

    html = ""

    def __init__(self, model, col, **kwargs):
        label = Label(model, col, alias=aliases.get(col, col))

    def set_alias(self, alias):
        self.alias = alias

    def set_cls_req(self, cls_req):
        self.cls_req = cls_req

    def set_cls_opt(self, cls_opt):
        self.cls_opt = cls_opt

    def set_cls_err(self, cls_err):
        self.cls_err = cls_err

    def set_cls_doc(self, cls_doc):
        self.cls_doc = cls_doc

class Label(object):
    """The `Label` class."""

    cls = None

    def __init__(self, model, col, **kwargs):
        self.name = col
        self.alias = kwargs.pop('alias', self.name)
        prettify = kwargs.pop('prettify', None)
        if callable(prettify):
            self.prettify = prettify

    def set_alias(self, alias):
        self.alias = alias

    def get_display(self):
        return self.prettify(self.alias)

    def prettify(text):
        return text.replace("_", " ").capitalize()

    prettify = staticmethod(prettify)

    def __str__(self):
        return h.content_tag("label", content=self.get_display(), for_=self.name, class_=self.cls)

class BaseField(object):
    """The `BaseField` class.

    This is the class that fits to all HTML <input> structure.

    """

    def __init__(self, name, value):
        self.name = name
        self.value = value

#    def __str__(self):
#        return h.text_field(self.name, value=self.value)

class Field(BaseField):
    """The `Field` class.

    This class takes a SQLAlchemy mapped class as first argument and the column
    name to process as second argument. It maps the column name to the field
    name and the column's value as the field's value.

    Method `get_value` will return either the current value (if not None) or
    the default value if available.

    All xField classes inherit of this `Field` class.

    """

    def __init__(self, model, col, **kwargs):
        super(Field, self).__init__(col, getattr(model, col))
        if model.c[col].default:
            self.default = model.c[col].default.arg
        else:
            self.default = model.c[col].default
        self.attribs = kwargs

    def get_value(self):
        if self.value is not None:
            return self.value
        else:
            return self.default

    def __str__(self):
        return h.text_field(self.name, value=self.value)

class TextField(Field):
    """The `TextField` class."""

    def __init__(self, model, col, **kwargs):
        super(TextField, self).__init__(model, col, **kwargs)
        self.length = model.c[col].type.length

    def __str__(self):
        return h.text_field(self.name, value=self.get_value(), maxlength=self.length, **self.attribs)

class PasswordField(TextField):
    """The `PasswordField` class."""

    def __str__(self):
        return h.password_field(self.name, value=self.get_value(), maxlength=self.length, **self.attribs)

class HiddenField(Field):
    """The `HiddenField` class."""

    def __str__(self):
        return h.hidden_field(self.name, value=self.get_value(), **self.attribs)

class BooleanField(Field):
    """The `BooleanField` class."""

    def __str__(self):
        return h.check_box(self.name, self.get_value(), checked=self.get_value(), **self.attribs)

class FileField(Field):
    """The `FileField` class."""

    def __str__(self):
        return h.file_field(self.name, value="foo", **self.attribs)

class IntegerField(Field):
    """The `IntegerField` class."""

    def __str__(self):
        return h.text_field(self.name, value=self.get_value(), **self.attribs)

class DateTimeField(Field):
    """The `DateTimeField` class."""

    def __str__(self):
        return h.text_field(self.name, value=self.get_value(), **self.attribs)


class DateField(Field):
    """The `DateField` class."""

    def __str__(self):
        return h.text_field(self.name, value=self.get_value(), **self.attribs)


class TimeField(Field):
    """The `TimeField` class."""

    def __str__(self):
        return h.text_field(self.name, value=self.get_value(), **self.attribs)

class RadioField(BaseField):
    """The `SelectField` class."""

    def __init__(self, name, value, **kwargs):
        super(RadioField, self).__init__(name, value)
        self.attribs = kwargs

    def __str__(self):
        return h.radio_button(self.name, self.value, **self.attribs)

class RadioSet(Field):
    """The `SelectField` class."""

    def __init__(self, model, col, choices, **kwargs):
        super(RadioSet, self).__init__(model, col, **kwargs)

        radios = []

        if isinstance(choices, dict):
            choices = choices.items()

        for choice in choices:
            # Choice is a list/tuple...
            if isinstance(choice, (list, tuple)):
                choice_name, choice_value = choice
                radio = RadioField(self.name, choice_value, checked=self.get_value() == choice_value)
                radios.append(str(radio) + choice_name)
            # ... or just a string.
            else:
                checked = choice == getattr(self.model, col) or choice == default
                radiofields.append("\n" + h.radio_button(col, choice, checked=checked) + choice)

        self.radios = radios

    def __str__(self):
        return h.tag("br").join(self.radios)

class DropDownField(Field):
    """The `DropDownField` class."""

    def __init__(self, model, col, options, **kwargs):
        self.options = options
        selected = kwargs.pop('selected', None)
        super(DropDownField, self).__init__(model, col, **kwargs)
        self.selected = selected or self.get_value()

    def __str__(self):
        return h.select(self.name, h.options_for_select(self.options, selected=self.selected), **self.attribs)