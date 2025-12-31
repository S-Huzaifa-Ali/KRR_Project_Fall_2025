from django.shortcuts import render
from django.http import JsonResponse
import emotion_pipeline
from .models import Movie
from django.views.decorators.csrf import csrf_exempt

def index(request):
    return render(request, 'index.html')

@csrf_exempt
def chat_api(request):
    if request.method == "POST":
        message = request.POST.get("message", "")
        if not message:
            return JsonResponse({"error": "No message provided"})
            
        emotion, tokens, scores = emotion_pipeline.classify(message)
        
        movies = Movie.objects.filter(predicted_emotion=emotion)

        movie_list = []
        for m in movies:
            score = 0.0
            if m.emotion_scores:
                parts = m.emotion_scores.split('|')
                for p in parts:
                    if ':' in p:
                        k, v = p.split(':')
                        if k.strip() == emotion:
                            try:
                                score = float(v)
                            except:
                                pass
                            break
            movie_list.append((m, score))
            
        movie_list.sort(key=lambda x: x[1], reverse=True)
        
        recommendations = [m[0] for m in movie_list[:3]]
        
        response_data = {
            "emotion": emotion,
            "movies": [
                {
                    "title": m.title,
                    "director": m.director,
                    "year": m.release_year,
                    "genre": m.genre,
                    "review_snippet": m.review[:100] + "..." if m.review else ""
                } for m in recommendations
            ]
        }
        return JsonResponse(response_data)
        
    return JsonResponse({"error": "Invalid request method"})
