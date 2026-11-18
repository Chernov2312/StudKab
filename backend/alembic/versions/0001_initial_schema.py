"""initial schema

Revision ID: 0001
Revises:
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "courses",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=160), nullable=False),
        sa.Column(
            "assessment_type",
            sa.Enum(
                "exam",
                "pass_fail",
                name="assessment_type",
                native_enum=False,
                create_constraint=True,
            ),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_courses")),
    )
    op.create_table(
        "groups",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_groups")),
        sa.UniqueConstraint("name", name=op.f("uq_groups_name")),
    )
    op.create_table(
        "instructors",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("display_name", sa.String(length=160), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_instructors")),
    )
    op.create_table(
        "login_attempts",
        sa.Column("key", sa.String(length=80), nullable=False),
        sa.Column("window", sa.DateTime(timezone=True), nullable=False),
        sa.Column("count", sa.Integer(), nullable=False),
        sa.CheckConstraint("count > 0", name=op.f("ck_login_attempts_positive_count")),
        sa.PrimaryKeyConstraint("key", "window", name=op.f("pk_login_attempts")),
    )
    op.create_index(op.f("ix_login_attempts_window"), "login_attempts", ["window"], unique=False)
    op.create_table(
        "request_types",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=160), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("fields_schema", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("comment_required", sa.Boolean(), nullable=False),
        sa.Column("comment_max_length", sa.Integer(), nullable=False),
        sa.CheckConstraint(
            "comment_max_length BETWEEN 1 AND 1000",
            name=op.f("ck_request_types_comment_max_length"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_request_types")),
        sa.UniqueConstraint("code", name=op.f("uq_request_types_code")),
    )
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("username", sa.String(length=64), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column(
            "role",
            sa.Enum("student", "staff", name="role", native_enum=False, create_constraint=True),
            nullable=False,
        ),
        sa.Column("active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
        sa.UniqueConstraint("username", name=op.f("uq_users_username")),
    )
    op.create_table(
        "course_offerings",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("course_id", sa.Uuid(), nullable=False),
        sa.Column("group_id", sa.Uuid(), nullable=False),
        sa.Column("instructor_id", sa.Uuid(), nullable=False),
        sa.Column("term", sa.String(length=32), nullable=False),
        sa.ForeignKeyConstraint(
            ["course_id"], ["courses.id"], name=op.f("fk_course_offerings_course_id_courses")
        ),
        sa.ForeignKeyConstraint(
            ["group_id"], ["groups.id"], name=op.f("fk_course_offerings_group_id_groups")
        ),
        sa.ForeignKeyConstraint(
            ["instructor_id"],
            ["instructors.id"],
            name=op.f("fk_course_offerings_instructor_id_instructors"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_course_offerings")),
    )
    op.create_index(
        op.f("ix_course_offerings_group_id"), "course_offerings", ["group_id"], unique=False
    )
    op.create_table(
        "sessions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("csrf_token", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_sessions_user_id_users")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_sessions")),
        sa.UniqueConstraint("token_hash", name=op.f("uq_sessions_token_hash")),
    )
    op.create_index(op.f("ix_sessions_user_id"), "sessions", ["user_id"], unique=False)
    op.create_table(
        "students",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("full_name", sa.String(length=160), nullable=False),
        sa.Column("faculty", sa.String(length=160), nullable=False),
        sa.Column("program", sa.String(length=160), nullable=False),
        sa.Column("course_year", sa.Integer(), nullable=False),
        sa.Column("group_id", sa.Uuid(), nullable=False),
        sa.CheckConstraint("course_year BETWEEN 1 AND 6", name=op.f("ck_students_course_year")),
        sa.ForeignKeyConstraint(
            ["group_id"], ["groups.id"], name=op.f("fk_students_group_id_groups")
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_students_user_id_users")),
        sa.PrimaryKeyConstraint("user_id", name=op.f("pk_students")),
    )
    op.create_index(op.f("ix_students_group_id"), "students", ["group_id"], unique=False)
    op.create_table(
        "applications",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("student_id", sa.Uuid(), nullable=False),
        sa.Column("type_id", sa.Uuid(), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "new",
                "in_progress",
                "ready",
                "rejected",
                name="status",
                native_enum=False,
                create_constraint=True,
            ),
            nullable=False,
        ),
        sa.Column("fields", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["student_id"], ["students.user_id"], name=op.f("fk_applications_student_id_students")
        ),
        sa.ForeignKeyConstraint(
            ["type_id"], ["request_types.id"], name=op.f("fk_applications_type_id_request_types")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_applications")),
    )
    op.create_index(
        "ix_applications_student_time",
        "applications",
        ["student_id", "created_at", "id"],
        unique=False,
    )
    op.create_table(
        "enrollments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("student_id", sa.Uuid(), nullable=False),
        sa.Column("offering_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["offering_id"],
            ["course_offerings.id"],
            name=op.f("fk_enrollments_offering_id_course_offerings"),
        ),
        sa.ForeignKeyConstraint(
            ["student_id"], ["students.user_id"], name=op.f("fk_enrollments_student_id_students")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_enrollments")),
        sa.UniqueConstraint("student_id", "offering_id", name=op.f("uq_enrollments_student_id")),
    )
    op.create_table(
        "exams",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("offering_id", sa.Uuid(), nullable=False),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("room", sa.String(length=80), nullable=False),
        sa.Column(
            "exam_type",
            sa.Enum(
                "exam", "pass_fail", name="exam_type", native_enum=False, create_constraint=True
            ),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["offering_id"],
            ["course_offerings.id"],
            name=op.f("fk_exams_offering_id_course_offerings"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_exams")),
    )
    op.create_index(
        "ix_exams_offering_time", "exams", ["offering_id", "scheduled_at"], unique=False
    )
    op.create_table(
        "lessons",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("offering_id", sa.Uuid(), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("room", sa.String(length=80), nullable=False),
        sa.Column(
            "lesson_type",
            sa.Enum(
                "lecture",
                "practice",
                "lab",
                "seminar",
                name="lesson_type",
                native_enum=False,
                create_constraint=True,
            ),
            nullable=False,
        ),
        sa.CheckConstraint("ends_at > starts_at", name=op.f("ck_lessons_time_range")),
        sa.ForeignKeyConstraint(
            ["offering_id"],
            ["course_offerings.id"],
            name=op.f("fk_lessons_offering_id_course_offerings"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_lessons")),
    )
    op.create_index(
        "ix_lessons_offering_start", "lessons", ["offering_id", "starts_at"], unique=False
    )
    op.create_table(
        "notifications",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("student_id", sa.Uuid(), nullable=False),
        sa.Column(
            "kind",
            sa.Enum(
                "schedule_change",
                "application_status",
                "deadline",
                "announcement",
                name="kind",
                native_enum=False,
                create_constraint=True,
            ),
            nullable=False,
        ),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column(
            "target_type",
            sa.Enum(
                "schedule",
                "exam",
                "request",
                name="target_type",
                native_enum=False,
                create_constraint=True,
            ),
            nullable=True,
        ),
        sa.Column("target_id", sa.Uuid(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "(target_type IS NULL) = (target_id IS NULL)", name=op.f("ck_notifications_target_pair")
        ),
        sa.ForeignKeyConstraint(
            ["student_id"], ["students.user_id"], name=op.f("fk_notifications_student_id_students")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_notifications")),
    )
    op.create_index(
        "ix_notifications_student_time",
        "notifications",
        ["student_id", "created_at", "id"],
        unique=False,
    )
    op.create_table(
        "application_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("application_id", sa.Uuid(), nullable=False),
        sa.Column(
            "from_status",
            sa.Enum(
                "new",
                "in_progress",
                "ready",
                "rejected",
                name="from_status",
                native_enum=False,
                create_constraint=True,
            ),
            nullable=True,
        ),
        sa.Column(
            "to_status",
            sa.Enum(
                "new",
                "in_progress",
                "ready",
                "rejected",
                name="to_status",
                native_enum=False,
                create_constraint=True,
            ),
            nullable=False,
        ),
        sa.Column("note", sa.Text(), nullable=False),
        sa.Column("actor_user_id", sa.Uuid(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["actor_user_id"], ["users.id"], name=op.f("fk_application_events_actor_user_id_users")
        ),
        sa.ForeignKeyConstraint(
            ["application_id"],
            ["applications.id"],
            name=op.f("fk_application_events_application_id_applications"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_application_events")),
    )
    op.create_index(
        "ix_application_events_application_time",
        "application_events",
        ["application_id", "created_at", "id"],
        unique=False,
    )
    op.create_table(
        "grades",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("enrollment_id", sa.Uuid(), nullable=False),
        sa.Column(
            "kind",
            sa.Enum("current", "final", name="kind", native_enum=False, create_constraint=True),
            nullable=False,
        ),
        sa.Column("value", sa.String(length=32), nullable=False),
        sa.Column("graded_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["enrollment_id"], ["enrollments.id"], name=op.f("fk_grades_enrollment_id_enrollments")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_grades")),
    )
    op.create_index(op.f("ix_grades_enrollment_id"), "grades", ["enrollment_id"], unique=False)
    op.create_table(
        "lesson_changes",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("lesson_id", sa.Uuid(), nullable=False),
        sa.Column(
            "kind",
            sa.Enum("moved", "cancelled", name="kind", native_enum=False, create_constraint=True),
            nullable=False,
        ),
        sa.Column("old_values", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "new_values", postgresql.JSONB(none_as_null=True, astext_type=sa.Text()), nullable=True
        ),
        sa.Column(
            "changed_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["lesson_id"], ["lessons.id"], name=op.f("fk_lesson_changes_lesson_id_lessons")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_lesson_changes")),
    )
    op.create_index(
        "ix_lesson_changes_lesson_time", "lesson_changes", ["lesson_id", "changed_at"], unique=False
    )


def downgrade() -> None:
    op.drop_index("ix_lesson_changes_lesson_time", table_name="lesson_changes")
    op.drop_table("lesson_changes")
    op.drop_index(op.f("ix_grades_enrollment_id"), table_name="grades")
    op.drop_table("grades")
    op.drop_index("ix_application_events_application_time", table_name="application_events")
    op.drop_table("application_events")
    op.drop_index("ix_notifications_student_time", table_name="notifications")
    op.drop_table("notifications")
    op.drop_index("ix_lessons_offering_start", table_name="lessons")
    op.drop_table("lessons")
    op.drop_index("ix_exams_offering_time", table_name="exams")
    op.drop_table("exams")
    op.drop_table("enrollments")
    op.drop_index("ix_applications_student_time", table_name="applications")
    op.drop_table("applications")
    op.drop_index(op.f("ix_students_group_id"), table_name="students")
    op.drop_table("students")
    op.drop_index(op.f("ix_sessions_user_id"), table_name="sessions")
    op.drop_table("sessions")
    op.drop_index(op.f("ix_course_offerings_group_id"), table_name="course_offerings")
    op.drop_table("course_offerings")
    op.drop_table("users")
    op.drop_table("request_types")
    op.drop_index(op.f("ix_login_attempts_window"), table_name="login_attempts")
    op.drop_table("login_attempts")
    op.drop_table("instructors")
    op.drop_table("groups")
    op.drop_table("courses")
