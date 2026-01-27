from django.http import HttpResponse
  
def index(request):
    return HttpResponse("Главная")
 
def about(request, name, age):
    return HttpResponse(f"""
                        О пользователе
                        Имя: {name}
                        Возраст: {age}
                        """)
 
def contact(request):
    return HttpResponse("Контакты")
