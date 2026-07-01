from django.test import TestCase
from django.contrib.auth.models import User
from decimal import Decimal
from usuarios.models import Perfil, Suscripcion, HistorialPeso, MetaUsuario, Notificacion
from planes.models import Plan
from datetime import date, timedelta
from django.utils import timezone
import uuid


class PerfilModelTest(TestCase):
    """Tests para el modelo Perfil"""
    
    def test_crear_perfil(self):
        """Test crear perfil de usuario - el signal ya lo crea automáticamente"""
        user = User.objects.create_user(username=f'testuser_{uuid.uuid4().hex[:8]}', password='testpass')
        # El señal ya creó el perfil, así que lo obtenemos
        perfil = Perfil.objects.get(user=user)
        self.assertEqual(perfil.user.username, user.username)
        self.assertEqual(perfil.rol, 'cliente')
    
    def test_calcular_imc(self):
        """Test cálculo de IMC"""
        user = User.objects.create_user(username=f'testuser_{uuid.uuid4().hex[:8]}', password='testpass')
        perfil = Perfil.objects.get(user=user)
        perfil.peso = Decimal('70.00')
        perfil.estatura = Decimal('1.70')
        perfil.save()
        
        imc = perfil.calcular_imc()
        self.assertAlmostEqual(imc, 24.2, places=1)
    
    def test_clasificacion_imc(self):
        """Test clasificación de IMC"""
        user = User.objects.create_user(username=f'testuser_{uuid.uuid4().hex[:8]}', password='testpass')
        perfil = Perfil.objects.get(user=user)
        
        # Normal
        perfil.peso = Decimal('70.00')
        perfil.estatura = Decimal('1.75')
        perfil.save()
        self.assertEqual(perfil.get_clasificacion_imc(), 'normal')
        
        # Sobrepeso
        perfil.peso = Decimal('90.00')
        perfil.save()
        self.assertEqual(perfil.get_clasificacion_imc(), 'sobrepeso')


class SuscripcionModelTest(TestCase):
    """Tests para el modelo Suscripcion"""
    
    def test_crear_suscripcion(self):
        """Test crear suscripción"""
        user = User.objects.create_user(username=f'testuser_{uuid.uuid4().hex[:8]}', password='testpass')
        plan = Plan.objects.create(
            nombre='Plan Mensual',
            precio=Decimal('50000'),
            descripcion='Plan de 30 días',
            duracion_dias=30
        )
        fecha_inicio = timezone.now().date()
        fecha_fin = fecha_inicio + timedelta(days=30)
        
        suscripcion = Suscripcion.objects.create(
            usuario=user,
            plan=plan,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            objetivo_rutina='mantener'
        )
        
        self.assertEqual(suscripcion.usuario.username, user.username)
        self.assertEqual(suscripcion.plan.nombre, 'Plan Mensual')
        self.assertTrue(suscripcion.activa)


class HistorialPesoModelTest(TestCase):
    """Tests para el modelo HistorialPeso"""
    
    def test_crear_registro_peso(self):
        """Test crear registro de peso"""
        user = User.objects.create_user(username=f'testuser_{uuid.uuid4().hex[:8]}', password='testpass')
        registro = HistorialPeso.objects.create(
            usuario=user,
            peso=Decimal('75.00'),
            estatura=Decimal('1.70')
        )
        
        self.assertIsNotNone(registro.imc)
        self.assertEqual(registro.get_clasificacion_imc(), 'Sobrepeso')
    
    def test_calculo_automatico_imc(self):
        """Test que el IMC se calcula automáticamente"""
        user = User.objects.create_user(username=f'testuser_{uuid.uuid4().hex[:8]}', password='testpass')
        registro = HistorialPeso.objects.create(
            usuario=user,
            peso=Decimal('70.00'),
            estatura=Decimal('1.70')
        )
        
        # IMC esperado: 70 / 1.7^2 = 24.22
        self.assertAlmostEqual(registro.imc, 24.2, places=1)


class MetaUsuarioModelTest(TestCase):
    """Tests para el modelo MetaUsuario"""
    
    def test_crear_meta(self):
        """Test crear meta de usuario"""
        user = User.objects.create_user(username=f'testuser_{uuid.uuid4().hex[:8]}', password='testpass')
        meta = MetaUsuario.objects.create(
            usuario=user,
            tipo='peso',
            descripcion='Bajar a 70 kg',
            peso_objetivo=Decimal('70.00')
        )
        
        self.assertEqual(meta.usuario.username, user.username)
        self.assertEqual(meta.estado, 'activa')
    
    def test_marcar_meta_completada(self):
        """Test marcar meta como completada"""
        user = User.objects.create_user(username=f'testuser_{uuid.uuid4().hex[:8]}', password='testpass')
        meta = MetaUsuario.objects.create(
            usuario=user,
            tipo='peso',
            descripcion='Bajar a 70 kg',
            peso_objetivo=Decimal('70.00')
        )
        
        meta.estado = 'completada'
        meta.fecha_completada = timezone.now()
        meta.save()
        
        self.assertEqual(meta.estado, 'completada')
        self.assertIsNotNone(meta.fecha_completada)


class NotificacionModelTest(TestCase):
    """Tests para el modelo Notificacion"""
    
    def test_crear_notificacion(self):
        """Test crear notificación"""
        user = User.objects.create_user(username=f'testuser_{uuid.uuid4().hex[:8]}', password='testpass')
        notificacion = Notificacion.objects.create(
            titulo='Stock bajo',
            mensaje='El producto está bajo',
            tipo='warning',
            usuario=user
        )
        
        self.assertEqual(notificacion.titulo, 'Stock bajo')
        self.assertFalse(notificacion.leida)
    
    def test_notificar_admins(self):
        """Test método de clase para notificar admins"""
        admin = User.objects.create_user(username=f'admin_{uuid.uuid4().hex[:8]}', password='adminpass', is_staff=True)
        
        count_before = Notificacion.objects.count()
        Notificacion.notificar_admins('Test', 'Mensaje de prueba', 'info')
        count_after = Notificacion.objects.count()
        
        self.assertEqual(count_after, count_before + 1)
    
    def test_crear_notificacion_global(self):
        """Test crear notificación sin usuario (global)"""
        notificacion = Notificacion.objects.create(
            titulo='Notificación global',
            mensaje='Mensaje para todos',
            tipo='info',
            usuario=None
        )
        
        self.assertIsNone(notificacion.usuario)
        self.assertEqual(notificacion.tipo, 'info')


class ViewTest(TestCase):
    """Tests básicos para vistas"""
    
    def test_login_view_exists(self):
        """Test que la vista de login existe"""
        from usuarios.views import iniciar_sesion
        self.assertIsNotNone(iniciar_sesion)
    
    def test_home_view_exists(self):
        """Test que la vista home existe"""
        from usuarios.views import home
        self.assertIsNotNone(home)
    
    def test_perfil_view_exists(self):
        """Test que la vista de perfil existe"""
        from usuarios.views import perfil_usuario
        self.assertIsNotNone(perfil_usuario)


class UtilsTest(TestCase):
    """Tests para utilitarios"""
    
    def test_obtener_frase_motivacional(self):
        """Test que obtener_frase_motivacional retorna formato correcto"""
        from usuarios.utils import obtener_frase_motivacional
        
        frase = obtener_frase_motivacional()
        
        self.assertIn('frase', frase)
        self.assertIn('autor', frase)
        self.assertIsInstance(frase['frase'], str)
        self.assertIsInstance(frase['autor'], str)
    
    def test_obtener_objetivo_usuario(self):
        """Test cálculo de objetivo según IMC"""
        from usuarios.utils import obtener_objetivo_usuario
        
        # Crear usuario de prueba
        user = User.objects.create_user(username=f'testobj_{uuid.uuid4().hex[:8]}', password='testpass')
        
        # Obtener el perfil que ya fue creado por el signal y actualizarlo
        perfil = Perfil.objects.get(user=user)
        perfil.peso = Decimal('80.00')
        perfil.estatura = Decimal('1.60')
        perfil.save()
        
        # Refrescar desde BD para obtener los valores actualizados
        perfil.refresh_from_db()
        
        # Verificar que los datos se guardaron
        self.assertEqual(perfil.peso, Decimal('80.00'))
        self.assertEqual(perfil.estatura, Decimal('1.60'))
        
        # Ahora el objetivo debería ser bajar_peso (IMC = 31.25 = obesidad)
        objetivo = obtener_objetivo_usuario(user)
        self.assertEqual(objetivo, 'bajar_peso')
