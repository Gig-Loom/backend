import os
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
from django.contrib.auth.decorators import login_required
from .models import Gig, GigImage
from accounts.models import User
from .serializers import GigSerializer
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_gig(request):
    try:
        if request.method == 'POST':
            title = request.POST.get('title')
            description = request.POST.get('description')
            price = request.POST.get('price')
            category = request.POST.get('category')
            location = request.POST.get('location')

            if not all([title, description, price, category, location]):
                return JsonResponse({
                    'success': False,
                    'error': 'All fields including are required.'
                }, status=400)

            gig = Gig.objects.create(
                title=title,
                description=description,
                price=float(price),
                category=category,
                location=location,
                creator=request.user
            )

            if 'images' not in request.FILES:
                return JsonResponse({
                    'success': False,
                    'error': 'At least one image is required.'
                }, status=400)

            images = request.FILES.getlist('images')

            for idx, image in enumerate(images):
                filename = f"{gig.id}_{idx}_{image.name}"
                image_path = os.path.join('uploads', filename)

                with default_storage.open(image_path, 'wb') as f:
                    for chunk in image.chunks():
                        f.write(chunk)
                        
                GigImage.objects.create(gig=gig, image=image_path)

            return JsonResponse({
                'success': True,
                'data': GigSerializer(gig).data
            }, status=201)

        return JsonResponse({
            'success': False,
            'error': 'Invalid request method.'
        }, status=405)

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_gigs(request):
    try:
        page = int(request.GET.get('page', 1))
        limit = int(request.GET.get('limit', 10))
        skip = (page - 1) * limit

        filter_kwargs = {'is_unlisted': False}
        category = request.GET.get('category')
        if category:
            filter_kwargs['category'] = category

        min_price = request.GET.get('minPrice')
        max_price = request.GET.get('maxPrice')
        if min_price or max_price:
            filter_kwargs['price__gte'] = min_price if min_price else 0
            filter_kwargs['price__lte'] = max_price if max_price else float('inf')

        search_query = request.GET.get('search')
        if search_query:
            filter_kwargs['title__icontains'] = search_query

        gigs = Gig.objects.filter(**filter_kwargs)[skip:skip + limit]

        total = Gig.objects.filter(**filter_kwargs).count()

        gigs_data = []
        for gig in gigs:
            gig_data = GigSerializer(gig).data
            gig_data['images'] = [image.image.url for image in gig.images.all()]
            gigs_data.append(gig_data)

        return JsonResponse({
            'success': True,
            'data': {
                'gigs': gigs_data,
                'total': total,
                'currentPage': page,
                'totalPages': (total // limit) + (1 if total % limit > 0 else 0),
                'hasMore': skip + len(gigs) < total
            }
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_gig_by_id(request, gig_id):
    try:
        gig = get_object_or_404(Gig, id=gig_id, is_unlisted=False)
        gig_data = GigSerializer(gig).data

        gig_data['images'] = [image.image.url for image in gig.images.all()]

        return JsonResponse({
            'success': True,
            'data': gig_data
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_gig(request, gig_id):
    try:
        gig = get_object_or_404(Gig, id=gig_id)

        if request.method == 'PUT':
            title = request.POST.get('title')
            description = request.POST.get('description')
            price = request.POST.get('price')
            category = request.POST.get('category')
            location = request.POST.get('location')
            replace_images = request.POST.get('replace_images') == 'true'

            if title:
                gig.title = title
            if description:
                gig.description = description
            if price:
                gig.price = price
            if category:
                gig.category = category
            if location:
                gig.location = location

            if 'images' in request.FILES:
                images = request.FILES.getlist('images')
                
                if replace_images:
                    for existing_image in gig.images.all():
                        if default_storage.exists(existing_image.image.name):
                            default_storage.delete(existing_image.image.name)
                        existing_image.delete()

                for idx, image in enumerate(images):
                    filename = f"{gig.id}_{idx}_{image.name}"
                    image_path = os.path.join('uploads', filename)

                    with default_storage.open(image_path, 'wb') as f:
                        for chunk in image.chunks():
                            f.write(chunk)

                    gig_image = GigImage(gig=gig, image=image_path)
                    gig_image.save()

            gig.save()

            updated_gig_data = GigSerializer(gig).data
            updated_gig_data['images'] = [image.image.url for image in gig.images.all()]

            return JsonResponse({
                'success': True,
                'data': updated_gig_data
            })

        return JsonResponse({
            'success': False,
            'error': 'Invalid request method.'
        }, status=405)

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_gig(request, gig_id):
    try:
        gig = get_object_or_404(Gig, id=gig_id)
        
        user = User.objects.filter(id=request.user.id).first()

        if user.id != gig.creator.id and not user.is_staff:
            return JsonResponse({
                'success': False,
                'error': 'You are not authorized to delete this gig.'
            }, status=403)  

        if gig.images.exists():
            for gig_image in gig.images.all(): 
                if default_storage.exists(gig_image.image.path):  
                    default_storage.delete(gig_image.image.path)  
                gig_image.delete()  

        gig.is_unlisted = True
        gig.save()

        return JsonResponse({
            'success': True,
            'message': 'Gig has been unlisted successfully'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
