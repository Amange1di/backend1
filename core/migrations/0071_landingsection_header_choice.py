from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [("core", "0070_remove_student_application_budget")]
    operations = [
        migrations.AlterField(
            model_name="landingsection",
            name="section_type",
            field=models.CharField(
                max_length=32,
                choices=[
                    ("header", "Header"),
                    ("hero", "Hero Section"),
                    ("about", "About Us"),
                    ("course_grid", "Course Grid"),
                    ("teacher_slider", "Teacher Slider"),
                    ("statistics", "Statistics"),
                    ("lead_form", "Lead Form"),
                    ("testimonials", "Testimonials"),
                    ("faq", "FAQ"),
                    ("pricing", "Pricing Table"),
                    ("video", "Video Block"),
                    ("gallery", "Gallery"),
                    ("contacts", "Contacts & Map"),
                    ("cta", "Call To Action"),
                    ("partners", "Partners"),
                    ("benefits", "Benefits"),
                ],
            ),
        ),
    ]
