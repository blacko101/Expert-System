from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = False

    dependencies = [
        ('support_app', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='DiagnosisLog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('opted_in', models.BooleanField(default=False)),
                ('facts', models.JSONField(default=dict)),
                ('results', models.JSONField(default=list)),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='auth.user')),
            ],
        ),
    ]
