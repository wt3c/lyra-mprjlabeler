from django import forms
from django.apps import apps
from django.forms.utils import flatatt
from django.template.loader import render_to_string
from django.templatetags.static import static
from django.utils.safestring import mark_safe


class QuillEditorWidget(forms.Textarea):

    """Widget used to render a QuillJS WYSIWYG."""

    class Media:
        js = (
            'https://cdn.rawgit.com/google/code-prettify/master/loader/run_prettify.js',
        )
        

    def render(self, name, value, attrs={}):
        """Render the Quill WYSIWYG."""
        if value is None:
            value = ''
        final_attrs = self.build_attrs(attrs, {'name': name})

        return mark_safe(render_to_string('labeler/widgets/quill.html', {
            'final_attrs': flatatt(final_attrs),
            'value': value,
            'id': final_attrs['id'],
        }))
