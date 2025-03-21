from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from datetime import date
from django.views.decorators.http import require_POST  # ✅ Add this line
from .models import *



def index(request):
    return render(request, "index.html")

def user_login(request):
    if request.user.is_authenticated:
        return redirect("/")
    else:
        if request.method == "POST":
            username = request.POST['username']
            password = request.POST['password']
            user = authenticate(username=username, password=password)

            if user is not None:
                user1 = Applicant.objects.get(user=user)
                if user1.type == "applicant":
                    login(request, user)
                    return redirect("/user_homepage")
            else:
                thank = True
                return render(request, "user_login.html", {"thank":thank})
    return render(request, "user_login.html")

def user_homepage(request):
    if not request.user.is_authenticated:
        return redirect('/user_login/')
    applicant = Applicant.objects.get(user=request.user)
    if request.method == "POST":   
        email = request.POST['email']
        first_name = request.POST['first_name']
        last_name = request.POST['last_name']
        phone = request.POST['phone']
        gender = request.POST['gender']

        applicant.user.email = email
        applicant.user.first_name = first_name
        applicant.user.last_name = last_name
        applicant.phone = phone
        applicant.gender = gender
        applicant.save()
        applicant.user.save()

        try:
            image = request.FILES['image']
            applicant.image = image
            applicant.save()
        except:
            pass
        alert = True
        applications = Application.objects.filter(applicant=applicant)
        return render(request, "user_homepage.html", {
            'alert': alert,
            'applications': applications,
            'applicant': applicant,  # <-- Add this line
        })

    applications = Application.objects.filter(applicant=applicant)
    return render(request, 'user_homepage.html', {
        'applications': applications,
        'applicant': applicant,  # <-- Add this line
    })

def all_jobs(request):
    jobs = Job.objects.all().order_by('-start_date')
    applicant = Applicant.objects.get(user=request.user)
    apply = Application.objects.filter(applicant=applicant)
    data = []
    for i in apply:
        data.append(i.job.id)
    return render(request, "all_jobs.html", {'jobs':jobs, 'data':data})

def job_detail(request, myid):
    job = Job.objects.get(id=myid)
    return render(request, "job_detail.html", {'job':job})

def job_apply(request, myid):
    if not request.user.is_authenticated:
        return redirect("/user_login")
    applicant = Applicant.objects.get(user=request.user)
    job = Job.objects.get(id=myid)
    date1 = date.today()
    if job.end_date < date1:
        closed = True
        return render(request, "job_apply.html", {'closed': closed})
    elif job.start_date > date1:
        notopen = True
        return render(request, "job_apply.html", {'notopen': notopen})
    else:
        if request.method == "POST":
            resume = request.FILES.get('resume')
            if resume:
                Application.objects.create(
                    job=job,
                    applicant=applicant,
                    resume=resume,
                    company=job.company  # 🔑 Add this line!
                )
                alert = True
                return render(request, "job_apply.html", {'alert': alert})
            else:
                error = "Resume file is required."
                return render(request, "job_apply.html", {'error': error, 'job': job})
    return render(request, "job_apply.html", {'job': job})


def signup(request):
    if request.method=="POST":   
        username = request.POST['username']
        first_name=request.POST['first_name']
        last_name=request.POST['last_name']
        password1 = request.POST['password1']
        password2 = request.POST['password2']
        phone = request.POST['phone']
        gender = request.POST['gender']
        image = request.FILES['image']

        if password1 != password2:
            messages.error(request, "Passwords do not match.")
            return redirect('/signup')
        
        user = User.objects.create_user(first_name=first_name, last_name=last_name, username=username, password=password1)
        applicants = Applicant.objects.create(user=user, phone=phone, gender=gender, image=image, type="applicant")
        user.save()
        applicants.save()
        return render(request, "user_login.html")
    return render(request, "signup.html")

def company_signup(request):
    if request.method == "POST":
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')
        phone = request.POST.get('phone', '').strip()
        gender = request.POST.get('gender', '')
        company_name = request.POST.get('company_name', '').strip()
        image = request.FILES.get('image')

        # Check for missing required fields
        if not all([username, email, first_name, last_name, password1, password2, phone, gender, company_name, image]):
            messages.error(request, "Please fill in all required fields.")
            return redirect('/company_signup')

        if password1 != password2:
            messages.error(request, "Passwords do not match.")
            return redirect('/company_signup')

        # Optional: Check if username or email already exists
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken.")
            return redirect('/company_signup')
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered.")
            return redirect('/company_signup')

        # Create user and company
        user = User.objects.create_user(
            first_name=first_name,
            last_name=last_name,
            email=email,
            username=username,
            password=password1
        )
        company = Company.objects.create(
            user=user,
            phone=phone,
            gender=gender,
            image=image,
            company_name=company_name,
            type="company",
            status="pending"
        )
        user.save()
        company.save()
        messages.success(request, "Registration successful. Please log in.")
        return redirect('/company_login')

    return render(request, "company_signup.html")

def company_login(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)

        if user is not None:
            user1 = Company.objects.get(user=user)
            if user1.type == "company" and user1.status != "pending":
                login(request, user)
                return redirect("/company_homepage")
        else:
            alert = True
            return render(request, "company_login.html", {"alert":alert})
    return render(request, "company_login.html")

def company_homepage(request):
    if not request.user.is_authenticated:
        return redirect("/company_login")
    company = Company.objects.get(user=request.user)
    if request.method=="POST":   
        email = request.POST['email']
        first_name=request.POST['first_name']
        last_name=request.POST['last_name']
        phone = request.POST['phone']
        gender = request.POST['gender']

        company.user.email = email
        company.user.first_name = first_name
        company.user.last_name = last_name
        company.phone = phone
        company.gender = gender
        company.save()
        company.user.save()

        try:
            image = request.FILES['image']
            company.image = image
            company.save()
        except:
            pass
        alert = True
        return render(request, "company_homepage.html", {'alert':alert})
    return render(request, "company_homepage.html", {'company':company})

def add_job(request):
    if not request.user.is_authenticated:
        return redirect("/company_login")
    if request.method == "POST":
        title = request.POST['job_title']
        start_date = request.POST['start_date']
        end_date = request.POST['end_date']
        salary = request.POST['salary']
        experience = request.POST['experience']
        location = request.POST['location']
        skills = request.POST['skills']
        description = request.POST['description']
        user = request.user
        company = Company.objects.get(user=user)
        job = Job.objects.create(company=company, title=title,start_date=start_date, end_date=end_date, salary=salary, image=company.image, experience=experience, location=location, skills=skills, description=description, creation_date=date.today())
        job.save()
        alert = True
        return render(request, "add_job.html", {'alert':alert})
    return render(request, "add_job.html")

def job_list(request):
    if not request.user.is_authenticated:
        return redirect("/company_login")
    companies = Company.objects.get(user=request.user)
    jobs = Job.objects.filter(company=companies)
    return render(request, "job_list.html", {'jobs':jobs})
def all_applicants(request):
    if not request.user.is_authenticated:
        return redirect("/company_login")
    company = Company.objects.get(user=request.user)
    application = Application.objects.filter(company=company).order_by('-apply_date')
    return render(request, "all_applicants.html", {'application': application})

def delete_job(request, id):
    job = Job.objects.get(id=id)
    job.delete()
    messages.success(request, "Job deleted successfully.")
    return redirect('job_list')

def accept_applicant(request, myid):
    application = get_object_or_404(Application, id=myid)
    application.status = 'Accepted'
    application.save()
    messages.success(request, f'{application.applicant.user.username} has been accepted!')
    return redirect('all_applicants')

@require_POST
def reject_applicant(request, myid):
    application = get_object_or_404(Application, id=myid)
    application.status = 'Rejected'
    application.save()
    messages.success(request, f'{application.applicant.user.username} has been rejected!')
    return redirect('all_applicants')


def edit_job(request, myid):
    if not request.user.is_authenticated:
        return redirect("/company_login")
    job = Job.objects.get(id=myid)
    if request.method == "POST":
        title = request.POST['job_title']
        start_date = request.POST['start_date']
        end_date = request.POST['end_date']
        salary = request.POST['salary']
        experience = request.POST['experience']
        location = request.POST['location']
        skills = request.POST['skills']
        description = request.POST['description']

        job.title = title
        job.salary = salary
        job.experience = experience
        job.location = location
        job.skills = skills
        job.description = description

        job.save()
        if start_date:
            job.start_date = start_date
            job.save()
        if end_date:
            job.end_date = end_date
            job.save()
        alert = True
        return render(request, "edit_job.html", {'alert':alert})
    return render(request, "edit_job.html", {'job':job})

def company_logo(request, myid):
    if not request.user.is_authenticated:
        return redirect("/company_login")
    job = Job.objects.get(id=myid)
    if request.method == "POST":
        image = request.FILES['logo']
        job.image = image 
        job.save()
        alert = True
        return render(request, "company_logo.html", {'alert':alert})
    return render(request, "company_logo.html", {'job':job})

def Logout(request):
    logout(request)
    return redirect('/')

def admin_login(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)

        if user.is_superuser:
            login(request, user)
            return redirect("/all_companies")
        else:
            alert = True
            return render(request, "admin_login.html", {"alert":alert})
    return render(request, "admin_login.html")

def view_applicants(request):
    if not request.user.is_authenticated:
        return redirect("/admin_login")
    applicants = Applicant.objects.all()
    return render(request, "view_applicants.html", {'applicants':applicants})

def delete_applicant(request, myid):
    if not request.user.is_authenticated:
        return redirect("/admin_login")
    applicant = User.objects.filter(id=myid)
    applicant.delete()
    return redirect("/view_applicants")

def pending_companies(request):
    if not request.user.is_authenticated:
        return redirect("/admin_login")
    companies = Company.objects.filter(status="pending")
    return render(request, "pending_companies.html", {'companies':companies})

def change_status(request, myid):
    if not request.user.is_authenticated:
        return redirect("/admin_login")
    company = Company.objects.get(id=myid)
    if request.method == "POST":
        status = request.POST['status']
        company.status=status
        company.save()
        alert = True
        return render(request, "change_status.html", {'alert':alert})
    return render(request, "change_status.html", {'company':company})

def accepted_companies(request):
    if not request.user.is_authenticated:
        return redirect("/admin_login")
    companies = Company.objects.filter(status="Accepted")
    return render(request, "accepted_companies.html", {'companies':companies})

def rejected_companies(request):
    if not request.user.is_authenticated:
        return redirect("/admin_login")
    companies = Company.objects.filter(status="Rejected")
    return render(request, "rejected_companies.html", {'companies':companies})

def all_companies(request):
    if not request.user.is_authenticated:
        return redirect("/admin_login")
    companies = Company.objects.all()
    return render(request, "all_companies.html", {'companies':companies})

def delete_company(request, myid):
    if not request.user.is_authenticated:
        return redirect("/admin_login")
    company = User.objects.filter(id=myid)
    company.delete()
    return redirect("/all_companies")
