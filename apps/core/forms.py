from django import forms

TAILWIND_INPUT = (
    'w-full border border-gray-300 rounded-lg px-3 py-2 '
    'focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition'
)


class TailwindFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, forms.CheckboxInput):
                widget.attrs['class'] = 'h-4 w-4 text-blue-600 border-gray-300 rounded'
            elif isinstance(widget, forms.Select):
                widget.attrs['class'] = TAILWIND_INPUT + ' bg-white'
            elif isinstance(widget, forms.Textarea):
                widget.attrs['class'] = TAILWIND_INPUT + ' resize-y'
            else:
                widget.attrs['class'] = TAILWIND_INPUT
