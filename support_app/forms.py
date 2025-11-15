# support_app/forms.py
from django import forms
import json

COMMON_BOOL_CHOICES = [('', '---'), ('true','Yes'), ('false','No')]

class DiagnoseForm(forms.Form):
    # Provide common structured fields; users can also paste JSON into advanced input
    ping_latency = forms.IntegerField(required=False, label='Ping (ms)')
    speed_mbps = forms.FloatField(required=False, label='Throughput (Mbps)')
    wifi_connected = forms.ChoiceField(choices=COMMON_BOOL_CHOICES, required=False, label='Wi-Fi Connected')
    ping_ip = forms.ChoiceField(choices=[('', '---'), ('success','success'), ('fail','fail')], required=False)
    ping_domain = forms.ChoiceField(choices=[('', '---'), ('success','success'), ('fail','fail')], required=False)
    gateway_ping = forms.ChoiceField(choices=[('', '---'), ('success','success'), ('fail','fail')], required=False)
    packet_loss = forms.IntegerField(required=False, label='Packet Loss (%)')
    rssi = forms.IntegerField(required=False, label='Wi-Fi RSSI (dBm)')
    cpu_temp = forms.IntegerField(required=False, label='CPU Temp (°C)')
    idle_cpu = forms.IntegerField(required=False, label='Idle CPU (%)')
    popups = forms.ChoiceField(choices=COMMON_BOOL_CHOICES, required=False, label='Frequent Popups')
    disk_health = forms.IntegerField(required=False, label='Disk Health (%)')
    app_crash = forms.ChoiceField(choices=COMMON_BOOL_CHOICES, required=False, label='App Crashes')
    ram_usage = forms.IntegerField(required=False, label='RAM Usage (%)')
    structured = forms.CharField(widget=forms.Textarea(attrs={'rows':4}), required=False,
                                 help_text="(Advanced) Paste JSON facts here, e.g. {\"ping_latency\":250}")
