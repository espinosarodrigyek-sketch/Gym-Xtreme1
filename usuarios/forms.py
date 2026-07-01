from django import forms
from .models import Rutina, Ejercicio


class RutinaForm(forms.ModelForm):
    """Formulario para crear y editar rutinas"""
    
    class Meta:
        model = Rutina
        fields = ['nombre', 'descripcion', 'nivel', 'duracion_dias', 'activa', 'imagen']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Nombre de la rutina'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-input',
                'rows': 3,
                'placeholder': 'Descripción de la rutina...'
            }),
            'nivel': forms.Select(attrs={'class': 'form-input'}),
            'duracion_dias': forms.NumberInput(attrs={
                'class': 'form-input',
                'min': '1',
                'placeholder': 'Días'
            }),
            'activa': forms.CheckboxInput(attrs={
                'style': 'width:20px;height:20px;'
            }),
            'imagen': forms.FileInput(attrs={
                'class': 'form-input',
                'accept': 'image/*'
            }),
        }
    
    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre', '').strip()
        if len(nombre) < 3:
            raise forms.ValidationError("El nombre debe tener al menos 3 caracteres")
        return nombre
    
    def clean_duracion_dias(self):
        duracion = self.cleaned_data.get('duracion_dias')
        if duracion and duracion < 1:
            raise forms.ValidationError("La duración debe ser al menos 1 día")
        return duracion


class EjercicioForm(forms.ModelForm):
    """Formulario para ejercicios individuales"""
    
    class Meta:
        model = Ejercicio
        fields = ['nombre', 'descripcion', 'series', 'repeticiones', 'descanso', 'dia', 'orden']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Nombre del ejercicio'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-input',
                'rows': 2,
                'placeholder': 'Instrucciones...'
            }),
            'series': forms.NumberInput(attrs={
                'class': 'form-input',
                'min': '1',
                'max': '20'
            }),
            'repeticiones': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Ej: 10-12'
            }),
            'descanso': forms.NumberInput(attrs={
                'class': 'form-input',
                'min': '0',
                'placeholder': 'Segundos'
            }),
            'dia': forms.Select(attrs={'class': 'form-input'}),
            'orden': forms.NumberInput(attrs={
                'class': 'form-input',
                'min': '1'
            }),
        }


class EjercicioInlineForm(forms.ModelForm):
    """Formulario para ejercicios inline en el formulario de rutina"""
    
    class Meta:
        model = Ejercicio
        fields = ['nombre', 'descripcion', 'series', 'repeticiones', 'descanso', 'dia', 'orden']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Ejercicio'
            }),
            'descripcion': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Descripción'
            }),
            'series': forms.NumberInput(attrs={
                'class': 'form-input',
                'style': 'width:60px'
            }),
            'repeticiones': forms.TextInput(attrs={
                'class': 'form-input',
                'style': 'width:80px',
                'placeholder': '10-12'
            }),
            'descanso': forms.NumberInput(attrs={
                'class': 'form-input',
                'style': 'width:60px',
                'placeholder': '60s'
            }),
            'dia': forms.Select(attrs={
                'class': 'form-input',
                'style': 'width:120px'
            }),
            'orden': forms.NumberInput(attrs={
                'class': 'form-input',
                'style': 'width:50px'
            }),
        }
