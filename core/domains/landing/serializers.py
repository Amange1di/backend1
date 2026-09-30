from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from core.models import (
    Company,
    Course,
    LandingHeaderLink,
    LandingPage,
    LandingSection,
    User,
)


class LandingSectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = LandingSection
        fields = (
            "id",
            "section_type",
            "order",
            "content",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "company",
            "company_id",
            "created_at",
            "updated_at",
        )


class LandingHeaderLinkSerializer(serializers.ModelSerializer):
    target_page_slug = serializers.CharField(
        source="target_page.slug",
        read_only=True,
    )
    target_page_title = serializers.CharField(
        source="target_page.title",
        read_only=True,
    )
    company_id = serializers.IntegerField(
        read_only=True,
    )

    class Meta:
        model = LandingHeaderLink
        fields = (
            "id",
            "label",
            "target_page",
            "target_page_slug",
            "target_page_title",
            "order",
            "company",
            "company_id",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "created_at",
            "updated_at",
        )

    def validate_target_page(self, value):
        request = self.context.get("request")
        user = request.user if request else None

        if (
            user
            and user.role == User.Role.COURSE_ADMIN
            and value.company
            and value.company != user.company
        ):
            raise serializers.ValidationError(
                _(
                    "You can only link to your own landing pages."
                )
            )
        return value


class LandingPageSerializer(serializers.ModelSerializer):
    sections = LandingSectionSerializer(
        many=True,
        required=False,
    )
    header_links = serializers.SerializerMethodField()
    owner = serializers.IntegerField(
        source="owner_id",
        read_only=True,
    )
    sections_count = serializers.SerializerMethodField()
    company_id = serializers.IntegerField(
        read_only=True,
    )

    class Meta:
        model = LandingPage
        fields = (
            "id",
            "title",
            "slug",
            "company",
            "company_id",
            "owner",
            "status",
            "moderation_comment",
            "submitted_at",
            "moderated_at",
            "published_at",
            "created_at",
            "updated_at",
            "sections_count",
            "sections",
            "header_links",
        )
        read_only_fields = (
            "company",
            "company_id",
            "owner",
            "status",
            "moderation_comment",
            "submitted_at",
            "moderated_at",
            "published_at",
            "created_at",
            "updated_at",
            "sections_count",
            "header_links",
        )

    def get_sections_count(self, obj):
        return obj.sections.count()

    def get_header_links(self, obj):
        links = (
            LandingHeaderLink.objects.filter(
                company=obj.company
            )
            .select_related("target_page")
        )
        return LandingHeaderLinkSerializer(
            links,
            many=True,
            context=self.context,
        ).data

    def validate_slug(self, value):
        candidate = (
            value or ""
        ).strip().lower()
        if not candidate:
            raise serializers.ValidationError(
                _("Slug is required.")
            )
        return candidate

    def validate_sections(self, value):
        request = self.context.get("request")
        user = request.user if request else None
        if (
            user
            and user.role == User.Role.COURSE_ADMIN
            and len(value) > user.max_blocks
        ):
            raise serializers.ValidationError(
                _(
                    "This admin cannot add more than %(limit)s blocks to one page."
                )
                % {"limit": user.max_blocks}
            )
        return value

    def _sync_sections(
        self,
        page: LandingPage,
        sections_data,
    ):
        if sections_data is None:
            return

        page.sections.all().delete()
        LandingSection.objects.bulk_create(
            [
                LandingSection(
                    page=page,
                    section_type=section[
                        "section_type"
                    ],
                    order=section.get(
                        "order",
                        index,
                    ),
                    content=section.get(
                        "content",
                        {},
                    ),
                )
                for index, section
                in enumerate(sections_data)
            ]
        )

    def create(self, validated_data):
        sections_data = validated_data.pop(
            "sections",
            [],
        )
        page = super().create(validated_data)
        self._sync_sections(
            page,
            sections_data,
        )
        return page

    def update(
        self,
        instance,
        validated_data,
    ):
        sections_data = validated_data.pop(
            "sections",
            None,
        )
        page = super().update(
            instance,
            validated_data,
        )
        self._sync_sections(
            page,
            sections_data,
        )
        return page


class LandingPublicSectionSerializer(
    serializers.ModelSerializer
):
    resolved_content = serializers.SerializerMethodField()

    class Meta:
        model = LandingSection
        fields = (
            "id",
            "section_type",
            "order",
            "content",
            "resolved_content",
        )

    def get_resolved_content(self, obj):
        content = dict(obj.content or {})
        company = obj.page.company

        if not company:
            return content

        if (
            obj.section_type
            == LandingSection.SectionType.COURSE_GRID
        ):
            content["courses"] = list(
                Course.objects.filter(
                    admins__company=company
                )
                .distinct()
                .values(
                    "id",
                    "title",
                    "price",
                    "duration_weeks",
                    "lesson_duration_minutes",
                    "description",
                )
            )

        elif (
            obj.section_type
            == LandingSection.SectionType.TEACHER_SLIDER
        ):
            content["teachers"] = list(
                User.objects.filter(
                    role=User.Role.TEACHER,
                    company=company,
                )
                .order_by(
                    "first_name",
                    "last_name",
                )
                .values(
                    "id",
                    "first_name",
                    "last_name",
                    "phone",
                    "telegram",
                    "working_hours",
                    "color",
                )
            )

        return content


class LandingPublicPageSerializer(
    serializers.ModelSerializer
):
    sections = LandingPublicSectionSerializer(
        many=True,
        read_only=True,
    )
    header_links = serializers.SerializerMethodField()
    company_data = serializers.SerializerMethodField()

    class Meta:
        model = LandingPage
        fields = (
            "id",
            "title",
            "slug",
            "company",
            "company_data",
            "status",
            "published_at",
            "sections",
            "header_links",
        )

    def get_header_links(self, obj):
        links = (
            LandingHeaderLink.objects.filter(
                company=obj.company,
                target_page__status=(
                    LandingPage.Status.ACTIVE
                ),
            )
            .select_related("target_page")
        )
        return LandingHeaderLinkSerializer(
            links,
            many=True,
            context=self.context,
        ).data

    def get_company_data(self, obj):
        if not obj.company:
            return None

        return {
            "id": obj.company.id,
            "name": obj.company.name,
            "slug": obj.company.slug,
            "phone": obj.company.phone,
            "telegram": obj.company.telegram,
            "whatsapp": obj.company.whatsapp,
            "address": obj.company.district,
            "website": obj.company.website,
            "instagram": getattr(
                obj.company,
                "instagram",
                None,
            ),
            "facebook": getattr(
                obj.company,
                "facebook",
                None,
            ),
        }
