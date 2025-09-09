from django.shortcuts import render
from .models import Category

def home(request):
    categories = Category.objects.all()
    return render(request, 'core/home.html', {'categories': categories})

from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.hashers import make_password

def register(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        confirm = request.POST['confirm_password']

        # Validate form
        if password != confirm:
            messages.error(request, "Passwords do not match.")
            return redirect('register')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect('register')

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists.")
            return redirect('register')

        # Save user
        User.objects.create(
            username=username,
            email=email,
            password=make_password(password)
        )
        messages.success(request, "Account created successfully. Please login.")
        return redirect('login')

    return render(request, 'core/register.html')
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome {username}!")
            return redirect('home')
        else:
            messages.error(request, "Invalid username or password.")
            return redirect('login')

    return render(request, 'core/login.html')


@login_required
def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('login')

from django.shortcuts import render
from .models import Quiz

def category_quizzes(request, category_id):
    quizzes = Quiz.objects.filter(category=category_id)
    return render(request, 'core/quizzes_by_category.html', {'quizzes': quizzes})
from django.shortcuts import get_object_or_404, redirect
from .models import Quiz, Question
from django.contrib.auth.decorators import login_required

@login_required
def start_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz, pk=quiz_id)
    questions = quiz.question_set.all()

    # Initialize quiz session
    request.session['quiz_id'] = quiz_id
    request.session['question_index'] = 0
    request.session['score'] = 0
    request.session['answers'] = {}

    return redirect('attempt_quiz')

from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from .models import Quiz, Option

@login_required
def attempt_quiz(request):
    quiz_id = request.session.get('quiz_id')
    question_index = request.session.get('question_index', 0)
    quiz = get_object_or_404(Quiz, pk=quiz_id)
    questions = quiz.question_set.all()

    # If all questions are answered, redirect to results
    if question_index >= len(questions):
        return redirect('quiz_result')

    current_question = questions[question_index]
    options = current_question.options.all()

    if request.method == 'POST':
        selected_option_id = request.POST.get('option')
        if selected_option_id:
            selected_option = Option.objects.get(id=selected_option_id)
            # Store user's answer
            answers = request.session.get('answers', {})
            answers[str(current_question.id)] = selected_option.id
            request.session['answers'] = answers

            # Update score if correct
            if selected_option.is_correct:
                request.session['score'] += 1

            # Move to next question
            request.session['question_index'] += 1
            return redirect('attempt_quiz')

    return render(request, 'core/quiz_attempt.html', {
        'question': current_question,
        'options': options,
        'question_number': question_index + 1,
        'total_questions': len(questions),
    })
from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import login_required
from .models import Quiz

from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import login_required
from .models import Quiz, Question, Option, Attempt, Answer

@login_required
def quiz_result(request):
    score = request.session.get('score', 0)
    quiz_id = request.session.get('quiz_id')
    quiz = get_object_or_404(Quiz, pk=quiz_id)
    total_questions = quiz.question_set.count()
    answers = request.session.get('answers', {})

    # Save the attempt
    attempt = Attempt.objects.create(
        user=request.user,
        quiz=quiz,
        score=score,
        total=total_questions,
    )

    # Save each answer
    for qid, oid in answers.items():
        question = Question.objects.get(pk=qid)
        option = Option.objects.get(pk=oid)
        Answer.objects.create(
            attempt=attempt,
            question=question,
            selected_option=option
        )

    # Clear session data
    for key in ['score', 'quiz_id', 'question_index', 'answers']:
        request.session.pop(key, None)

    return render(request, 'core/quiz_result.html', {
        'score': score,
        'total_questions': total_questions,
        'quiz': quiz
    })

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Attempt

@login_required
def my_attempts(request):
    attempts = Attempt.objects.filter(user=request.user).order_by('-completed_at')
    return render(request, 'core/my_attempts.html', {'attempts': attempts})

from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count
from .models import User, Quiz, Attempt

@staff_member_required
def admin_dashboard(request):
    context = {
        'total_users': User.objects.count(),
        'total_quizzes': Quiz.objects.count(),
        'total_attempts': Attempt.objects.count(),
        'top_quizzes': Quiz.objects.annotate(
            attempts=Count('attempt')
        ).order_by('-attempts')[:5],
    }
    return render(request, 'core/admin_dashboard.html', context)

from django.contrib.auth.models import User
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
import csv
from io import TextIOWrapper

@staff_member_required
def admin_manage_users(request):
    users = User.objects.all()
    return render(request, 'core/admin_users.html', {'users': users})

@staff_member_required
def admin_add_user(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
        else:
            User.objects.create_user(username=username, email=email, password=password)
            messages.success(request, "User created successfully.")
            return redirect('admin_manage_users')
    
    return render(request, 'core/admin_add_user.html')

@staff_member_required
def delete_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    user.delete()
    messages.success(request, "User deleted successfully.")
    return redirect('admin_manage_users')

@staff_member_required
def upload_users_csv(request):
    if request.method == 'POST' and request.FILES.get('csv_file'):
        csv_file = request.FILES['csv_file']
        file_data = TextIOWrapper(csv_file.file, encoding='utf-8')
        reader = csv.DictReader(file_data)
        
        for row in reader:
            username = row.get('username')
            email = row.get('email')
            password = row.get('password')
            
            if username and not User.objects.filter(username=username).exists():
                User.objects.create_user(username=username, email=email, password=password)
        
        messages.success(request, "Users uploaded successfully.")
        return redirect('admin_manage_users')
    
    return render(request, 'core/admin_upload_users.html')

@staff_member_required
def edit_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        user.username = request.POST.get('username')
        user.email = request.POST.get('email')
        password = request.POST.get('password')
        
        if password:
            user.set_password(password)
        
        user.save()
        messages.success(request, "User updated successfully.")
        return redirect('admin_manage_users')
    
    return render(request, 'core/admin_edit_user.html', {'user': user})
from .models import Quiz, Category
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
import csv
from io import TextIOWrapper

@staff_member_required
def admin_manage_quizzes(request):
    quizzes = Quiz.objects.all()
    return render(request, 'core/admin_quizzes.html', {'quizzes': quizzes})

@staff_member_required
def admin_add_quiz(request):
    categories = Category.objects.all()
    if request.method == 'POST':
        title = request.POST.get('title')
        category_id = request.POST.get('category')
        status = request.POST.get('status')
        category = get_object_or_404(Category, id=category_id)
        Quiz.objects.create(title=title, category=category, status=status)
        messages.success(request, "Quiz added successfully.")
        return redirect('admin_manage_quizzes')
    return render(request, 'core/admin_add_quiz.html', {'categories': categories})

@staff_member_required
def admin_edit_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    categories = Category.objects.all()
    if request.method == 'POST':
        quiz.title = request.POST.get('title')
        category_id = request.POST.get('category')
        quiz.category = get_object_or_404(Category, id=category_id)
        quiz.status = request.POST.get('status')
        quiz.save()
        messages.success(request, "Quiz updated successfully.")
        return redirect('admin_manage_quizzes')
    return render(request, 'core/admin_edit_quiz.html', {'quiz': quiz, 'categories': categories})

@staff_member_required
def admin_delete_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    quiz.delete()
    messages.success(request, "Quiz deleted.")
    return redirect('admin_manage_quizzes')

@staff_member_required
def upload_quizzes_csv(request):
    if request.method == 'POST':
        csv_file = request.FILES['csv_file']
        file_data = TextIOWrapper(csv_file.file, encoding='utf-8')
        reader = csv.DictReader(file_data)
        for row in reader:
            category_name = row['category']
            category, _ = Category.objects.get_or_create(name=category_name)
            Quiz.objects.create(
                title=row['title'],
                category=category,
                status=row.get('status', 'active')
            )
        messages.success(request, "Quizzes uploaded successfully.")
        return redirect('admin_manage_quizzes')
    return render(request, 'core/admin_upload_quizzes.html')

from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Quiz, Question

@login_required
def start_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    if quiz.status != 'active':
        messages.warning(request, "This quiz is not currently active.")
        return redirect('quizzes_by_category')

    questions = Question.objects.filter(quiz=quiz).order_by('?')
    return render(request, 'core/quiz_attempt.html', {
        'quiz': quiz,
        'questions': questions,
        'total_questions': questions.count()
    })


