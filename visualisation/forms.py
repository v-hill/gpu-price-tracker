from django import forms

from .models import GraphicsCard


class GraphicsCardForm(forms.ModelForm):
    class Meta:
        model = GraphicsCard
        fields = ["model", "memory_size"]
