from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Course, Subject
from .forms import CourseForm, SubjectForm


# --------- CURSOS ---------
@login_required
def course_list(request):
    courses = Course.objects.filter(is_active=True)
    return render(request, 'courses/course_list.html', {'courses': courses})

@login_required
def course_detail(request, pk):
    course = get_object_or_404(Course, pk=pk)
    return render(request, 'courses/course_detail.html', {'course': course})

@login_required
def course_create(request):
    if request.method == 'POST':
        form = CourseForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('courses:course_list')
    else:
        form = CourseForm()
    return render(request, 'courses/course_form.html', {'form': form})

@login_required
def course_edit(request, pk):
    course = get_object_or_404(Course, pk=pk)
    if request.method == 'POST':
        form = CourseForm(request.POST, instance=course)
        if form.is_valid():
            form.save()
            return redirect('courses:course_detail', pk=pk)
    else:
        form = CourseForm(instance=course)
    return render(request, 'courses/course_form.html', {'form': form, 'is_edit': True, 'course': course})

@login_required
def course_delete(request, pk):
    course = get_object_or_404(Course, pk=pk)
    if request.method == 'POST':
        course.delete()
        return redirect('courses:course_list')
    return render(request, 'courses/course_confirm_delete.html', {'course': course})


# --------- MATERIAS ---------
@login_required
def subject_list(request):
    subjects = Subject.objects.filter(is_active=True).select_related('course', 'teacher')
    return render(request, 'courses/subject_list.html', {'subjects': subjects})

@login_required
def subject_detail(request, pk):
    subject = get_object_or_404(Subject, pk=pk)
    return render(request, 'courses/subject_detail.html', {'subject': subject})

@login_required
def subject_create(request):
    if request.method == 'POST':
        form = SubjectForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('courses:subject_list')
    else:
        form = SubjectForm()
    return render(request, 'courses/subject_form.html', {'form': form})

@login_required
def subject_edit(request, pk):
    subject = get_object_or_404(Subject, pk=pk)
    if request.method == 'POST':
        form = SubjectForm(request.POST, instance=subject)
        if form.is_valid():
            form.save()
            return redirect('courses:subject_detail', pk=pk)
    else:
        form = SubjectForm(instance=subject)
    return render(request, 'courses/subject_form.html', {'form': form, 'is_edit': True, 'subject': subject})

@login_required
def subject_delete(request, pk):
    subject = get_object_or_404(Subject, pk=pk)
    if request.method == 'POST':
        subject.delete()
        return redirect('courses:subject_list')
    return render(request, 'courses/subject_confirm_delete.html', {'subject': subject})
