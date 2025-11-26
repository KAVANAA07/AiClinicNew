from django.contrib import admin
from django.utils.html import format_html
from .models import State, District, Clinic, Doctor, Patient, Token, Consultation, Receptionist, DoctorSchedule, PrescriptionItem

class ClinicAdmin(admin.ModelAdmin):
    list_display = ['name', 'city', 'district', 'latitude', 'longitude', 'map_link']
    list_filter = ['district', 'city']
    search_fields = ['name', 'city', 'address']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'address', 'city', 'district')
        }),
        ('GPS Coordinates', {
            'fields': ('latitude', 'longitude', 'coordinate_helper'),
            'description': 'Use the links below to get accurate coordinates'
        }),
    )
    
    readonly_fields = ['coordinate_helper']
    
    def coordinate_helper(self, obj):
        """Display interactive map for coordinate selection"""
        lat = obj.latitude or 12.9716
        lng = obj.longitude or 77.5946
        
        return format_html('''
        <div style="background: #f8f9fa; padding: 15px; border: 1px solid #dee2e6; border-radius: 5px;">
            <h4>Click on Map to Set Coordinates:</h4>
            
            <div id="map-container" style="margin: 10px 0;">
                <iframe id="coord-map" 
                    src="https://www.openstreetmap.org/export/embed.html?bbox={},{},{},{}&layer=mapnik&marker={},{}" 
                    width="100%" height="300" 
                    style="border: 1px solid #ccc; border-radius: 5px;">
                </iframe>
            </div>
            
            <div style="margin: 10px 0; padding: 10px; background: white; border-radius: 3px;">
                <strong>Selected Coordinates:</strong> 
                <span id="selected-coords">{}, {}</span><br>
                <a href="/api/coordinate-picker/?lat={}&lng={}" target="_blank" 
                   style="background: #007cba; color: white; padding: 8px 15px; text-decoration: none; border-radius: 3px; margin-top: 5px; display: inline-block;">
                    📍 Click to Select Location
                </a>
            </div>
            
            <div style="background: #d4edda; padding: 10px; border-radius: 3px; margin-top: 10px;">
                <strong>Instructions:</strong><br>
                1. Click "Click to Select Location" button<br>
                2. Click on your clinic's exact location on the map<br>
                3. Coordinates will auto-fill in the fields above<br>
                4. Click Save to update
            </div>
        </div>
        
        <script>
        // Auto-fill coordinates if available in URL
        function checkForCoordinates() {{
            var urlParams = new URLSearchParams(window.location.search);
            var lat = urlParams.get('lat');
            var lng = urlParams.get('lng');
            
            if (lat && lng) {{
                document.getElementById('id_latitude').value = lat;
                document.getElementById('id_longitude').value = lng;
                document.getElementById('selected-coords').innerHTML = lat + ', ' + lng;
            }}
        }}
        
        // Check for coordinates when page loads
        setTimeout(checkForCoordinates, 500);
        </script>
        ''', lng-0.01, lat-0.01, lng+0.01, lat+0.01, lat, lng, lat, lng, lat, lng, lat, lng)
    
    coordinate_helper.short_description = "Interactive Map Selector"
    
    def map_link(self, obj):
        """Show link to view location on Google Maps"""
        if obj.latitude and obj.longitude:
            url = f"https://maps.google.com/maps?q={obj.latitude},{obj.longitude}"
            return format_html('<a href="{}" target="_blank">📍 View</a>', url)
        return "No coordinates"
    
    map_link.short_description = "Map"

class TokenAdmin(admin.ModelAdmin):
    list_display = ['token_number', 'patient', 'doctor', 'date', 'appointment_time', 'status', 'distance_km']
    list_filter = ['status', 'date', 'doctor', 'clinic']
    search_fields = ['patient__name', 'doctor__name', 'token_number']
    readonly_fields = ['distance_km', 'created_at', 'completed_at', 'arrival_confirmed_at']

class DoctorAdmin(admin.ModelAdmin):
    list_display = ['name', 'specialization', 'clinic']
    list_filter = ['specialization', 'clinic']
    search_fields = ['name', 'specialization']

class PatientAdmin(admin.ModelAdmin):
    list_display = ['name', 'age', 'phone_number', 'user']
    search_fields = ['name', 'phone_number']

class ConsultationAdmin(admin.ModelAdmin):
    list_display = ['patient', 'doctor', 'date']
    list_filter = ['doctor', 'date']
    search_fields = ['patient__name', 'doctor__name']

# Register models
admin.site.register(State)
admin.site.register(District)
admin.site.register(Clinic, ClinicAdmin)
admin.site.register(Doctor, DoctorAdmin)
admin.site.register(Patient, PatientAdmin)
admin.site.register(Token, TokenAdmin)
admin.site.register(Consultation, ConsultationAdmin)
admin.site.register(Receptionist)
admin.site.register(DoctorSchedule)
admin.site.register(PrescriptionItem)

# Customize admin site
admin.site.site_header = "MedQ Clinic Management"
admin.site.site_title = "MedQ Admin"
admin.site.index_title = "Welcome to MedQ Administration"