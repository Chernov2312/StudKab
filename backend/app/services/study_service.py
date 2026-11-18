from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.domain import Assessment, GradeKind, Result
from app.db.dao.study_dao import StudyDAO
from app.db.models import Enrollment, Grade
from app.schemas.study import CourseResult, GradeItem, Study, Summary


def final_grade(grades: list[Grade]) -> str | None:
    return next((grade.value for grade in reversed(grades) if grade.kind == GradeKind.FINAL), None)


def assessment_result(kind: Assessment, value: str | None) -> Result:
    if value is None:
        return Result.PENDING
    passing = {"зачёт", "зачет"} if kind == Assessment.PASS_FAIL else {"3", "4", "5"}
    return Result.PASSED if value.strip().casefold() in passing else Result.FAILED


def course_result(enrollment: Enrollment) -> CourseResult:
    course = enrollment.offering.course
    final = final_grade(enrollment.grades)
    return CourseResult(
        offering_id=enrollment.offering_id,
        title=course.title,
        assessment_type=course.assessment_type,
        final_grade=final,
        result=assessment_result(course.assessment_type, final),
        grades=[GradeItem.model_validate(grade) for grade in enrollment.grades],
    )


async def get_study(db: AsyncSession, student_id: UUID) -> Study:
    courses = [
        course_result(enrollment)
        for enrollment in await StudyDAO(db).list_enrollments_with_grades(student_id)
    ]
    return Study(
        summary=Summary(
            passed=sum(course.result == Result.PASSED for course in courses),
            total=len(courses),
            pending=sum(course.result == Result.PENDING for course in courses),
        ),
        courses=courses,
    )
