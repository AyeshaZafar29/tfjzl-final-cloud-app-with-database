from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseRedirect
from .models import Course, Enrollment, Submission, Choice 
from django.contrib.auth.models import User
from django.urls import reverse
from django.views import generic
from django.contrib.auth import login, logout, authenticate
import logging

logger = logging.getLogger(__name__)

# --- Registration, Login, Logout functions ---

def registration_request(request):
    # Context mein unnecessary variables hata diye hain
    context = {}
    if request.method == 'GET':
        return render(request, 'onlinecourse/user_registration_bootstrap.html', context)
    elif request.method == 'POST':
        username = request.POST['username']
        password = request.POST['psw']
        first_name = request.POST['firstname']
        last_name = request.POST['lastname']
        user_exist = False
        try:
            User.objects.get(username=username)
            user_exist = True
        except:
            logger.error("New user")
        if not user_exist:
            user = User.objects.create_user(username=username, first_name=first_name, last_name=last_name, password=password)
            login(request, user)
            return redirect("onlinecourse:index")
        else:
            context['message'] = "User already exists."
            return render(request, 'onlinecourse/user_registration_bootstrap.html', context)

def login_request(request):
    context = {}
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['psw']
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('onlinecourse:index')
        else:
            context['message'] = "Invalid username or password."
            return render(request, 'onlinecourse/user_login_bootstrap.html', context)
    else:
        return render(request, 'onlinecourse/user_login_bootstrap.html', context)

def logout_request(request):
    logout(request)
    return redirect('onlinecourse:index')

def check_if_enrolled(user, course):
    return Enrollment.objects.filter(user=user, course=course).exists()

class CourseListView(generic.ListView):
    template_name = 'onlinecourse/course_list_bootstrap.html'
    context_object_name = 'course_list'
    def get_queryset(self):
        return Course.objects.order_by('-total_enrollment')[:10]

class CourseDetailView(generic.DetailView):
    model = Course
    template_name = 'onlinecourse/course_detail_bootstrap.html'

def enroll(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    if not check_if_enrolled(request.user, course) and request.user.is_authenticated:
        Enrollment.objects.create(user=request.user, course=course, mode='honor')
        course.total_enrollment += 1
        course.save()
    return HttpResponseRedirect(reverse('onlinecourse:course_details', args=(course.id,)))

# --- Exam Logic Functions ---

def extract_answers(request):
    submitted_answers = []
    for key in request.POST:
        if key.startswith('choice_'):
            value = request.POST[key]
            submitted_answers.append(int(value))
    return submitted_answers

def submit(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    enrollment = Enrollment.objects.get(user=request.user, course=course)
    submission = Submission.objects.create(enrollment=enrollment)
    
    choice_ids = extract_answers(request)
    for choice_id in choice_ids:
        choice = Choice.objects.get(pk=choice_id)
        submission.choices.add(choice)
    submission.save()
    
    return redirect(reverse('onlinecourse:result', args=(submission.id,)))

def show_exam_result(request, submission_id):
    submission = get_object_or_404(Submission, pk=submission_id)
    course = submission.enrollment.course
    
    # Grade Calculation Logic
    correct_choices = submission.choices.filter(is_correct=True).count()
    total_questions = course.question_set.count()
    
    grade = 0
    if total_questions > 0:
        grade = (correct_choices / total_questions) * 100
        
    context = {
        'submission': submission,
        'course': course,
        'grade': grade
    }
    return render(request, 'onlinecourse/exam_result_bootstrap.html', context)