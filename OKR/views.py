import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.shortcuts import render, redirect
from .forms import EntryCreationForm, ObjectiveCreationForm, KRCreationForm
from .models import Entry, Objective, KR
from .filters import ObjectiveKRFilter
from django.shortcuts import get_object_or_404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


@login_required
def view_data(request):
    if request.method == 'POST' and 'objective-btn' in request.POST:
        form = ObjectiveCreationForm(request.POST)
        if form.is_valid():
            objective = form.save(commit=False)
            objective.user = get_object_or_404(User, id=request.user.id)
            objective.save()
            messages.success(request, 'Objective Created successfully')
            return redirect('okr-view-data')
    if request.method == 'POST' and 'entry-btn' in request.POST:
        form = EntryCreationForm(request.POST)
        if form.is_valid():
            entry = form.save(commit=False)
            time_spent = entry.time_spent
            kr = entry.key_result.id
            entry.user = get_object_or_404(User, id=request.user.id)
            entry.save()
            kr = get_object_or_404(KR,id=kr)
            prev_percentage = kr.percentage
            percentage = round(((((prev_percentage/100)*kr.hours*60)+time_spent)/(kr.hours*60))*100)
            kr.percentage = percentage
            print(kr.percentage)
            kr.save()
            messages.success(request, 'Entry Created successfully')
            return redirect('okr-view-data')
    if request.method == 'POST' and 'kr-btn' in request.POST:
        form = KRCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Key Result Created successfully')
            return redirect('okr-view-data')
    if request.is_ajax():
        obj_id = request.GET.get('objective_id')
        krs = KR.objects.filter(objective_id=obj_id)
        return JsonResponse(list(krs.values('id', 'key_result')), safe=False)
    form_objective = ObjectiveCreationForm()
    form_kr = KRCreationForm()
    user = get_object_or_404(User, id=request.user.id)
    form_kr.fields['objective'].queryset = Objective.objects.filter(user=user)
    form_entry = EntryCreationForm()
    form_entry.fields['objective'].queryset = Objective.objects.filter(user=user)
    data = Entry.objects.filter(user=request.user).order_by('-date_time')
    form = ObjectiveKRFilter(request.GET, queryset=data)
    data = form.qs

    paginator = Paginator(data, 10)

    page = request.GET.get('page')
    try:
        response = paginator.page(page)
    except PageNotAnInteger:
        response = paginator.page(1)
    except EmptyPage:
        response = paginator.page(paginator.num_pages)

    krs = KR.objects.filter(objective__user=user)
    context = {
        'show': True,
        'krs': krs,
        'data': response,
        'form_kr': form_kr,
        'form_objective': form_objective,
        'form_entry': form_entry,
        'filter_form': form
    }
    return render(request, 'OKR/show_entry.html', context=context)


@login_required
def load_okr(request, id):
    if id == request.user.id:
        return redirect('okr-view-data')
    user = get_object_or_404(User, id=id)
    data = Entry.objects.filter(user=user)
    context = {
        'show': False,
        'id': id,
        'data': data
    }
    return render(request, 'webpages/index.html', context=context)

