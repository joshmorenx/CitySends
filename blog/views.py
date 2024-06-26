from django.shortcuts import render, get_object_or_404, redirect
from blog.models import Post, Comment, Preference, Reflejado, Hashtags
from users.models import Follow, Profile
import sys
from django.contrib.auth.models import User
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Count
from .forms import NewCommentForm
from django.contrib.auth.decorators import login_required
from .serializers import UserSerializer, GroupSerializer, PostSerializer
from django.contrib.auth.models import User, Group
from rest_framework import viewsets
from rest_framework import permissions
from rest_framework.decorators import api_view
from django.http.response import JsonResponse
from rest_framework.parsers import JSONParser 
from rest_framework import status
from django import forms
#=================================================================================================================>
import pandas as pd
import re
import geopandas as gpd
from shapely import wkt
from shapely.geometry import Polygon, Point

df = pd.read_csv('poligonos_mx.csv') #Se lee el csv como un dataframe normal y después se convierte a geodataframe
df['geometry'] = df['geometry'].apply(wkt.loads)
gdf = gpd.GeoDataFrame(df, crs='epsg:4326')

def dime_estado(lon, lat):
    estado = 'Fuera de México'
    band = 0
    point = Point(lon, lat)
    for index, row in gdf.iterrows():
        poligon = gdf['geometry'][index]
        if poligon.contains(point):
            estado = gdf['estado'][index]
            band = 1
            break
    return estado

def is_users(post_user, logged_user):
    return post_user == logged_user


PAGINATION_COUNT = 3


class PostListView(LoginRequiredMixin, ListView):
    model = Post
    template_name = 'blog/home.html'
    context_object_name = 'posts'
    ordering = ['-date_posted']
    paginate_by = PAGINATION_COUNT

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)

        all_users = []
        data_counter = Post.objects.values('author')\
            .annotate(author_count=Count('author'))\
            .order_by('-author_count')[:6]

        for aux in data_counter:
            all_users.append(User.objects.filter(pk=aux['author']).first())
        # if Preference.objects.get(user = self.request.user):
        #     data['preference'] = True
        # else:
        #     data['preference'] = False
        data['preference'] = Preference.objects.all()
        # print(Preference.objects.get(user= self.request.user))
        data['all_users'] = all_users
        print(all_users, file=sys.stderr)
        return data

    def get_queryset(self):
        user = self.request.user
        qs = Follow.objects.filter(user=user)
        follows = [user]
        for obj in qs:
            follows.append(obj.follow_user)
        return Post.objects.filter(author__in=follows).order_by('-date_posted')


class UserPostListView(LoginRequiredMixin, ListView):
    model = Post
    template_name = 'blog/user_posts.html'
    context_object_name = 'posts'
    paginate_by = PAGINATION_COUNT

    def visible_user(self):
        return get_object_or_404(User, username=self.kwargs.get('username'))

    def get_context_data(self, **kwargs):
        visible_user = self.visible_user()
        logged_user = self.request.user
        print(logged_user.username == '', file=sys.stderr)

        if logged_user.username == '' or logged_user is None:
            can_follow = False
        else:
            can_follow = (Follow.objects.filter(user=logged_user,
                                                follow_user=visible_user).count() == 0)
        data = super().get_context_data(**kwargs)

        data['user_profile'] = visible_user
        data['can_follow'] = can_follow
        return data

    def get_queryset(self):
        user = self.visible_user()
        return Post.objects.filter(author=user).order_by('-date_posted')

    def post(self, request, *args, **kwargs):
        if request.user.id is not None:
            follows_between = Follow.objects.filter(user=request.user,
                                                    follow_user=self.visible_user())

            if 'follow' in request.POST:
                    new_relation = Follow(user=request.user, follow_user=self.visible_user())
                    if follows_between.count() == 0:
                        new_relation.save()
            elif 'unfollow' in request.POST:
                    if follows_between.count() > 0:
                        follows_between.delete()

        return self.get(self, request, *args, **kwargs)


class PostDetailView(DetailView):
    model = Post
    template_name = 'blog/post_detail.html'
    context_object_name = 'post'

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        comments_connected = Comment.objects.filter(post_connected=self.get_object()).order_by('-date_posted')
        data['comments'] = comments_connected
        data['form'] = NewCommentForm(instance=self.request.user)
        return data

    def post(self, request, *args, **kwargs):
        new_comment = Comment(content=request.POST.get('content'),
                              author=self.request.user,
                              post_connected=self.get_object())
        new_comment.save()

        return self.get(self, request, *args, **kwargs)


class PostDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Post
    template_name = 'blog/post_delete.html'
    context_object_name = 'post'
    success_url = '/'

    def test_func(self):
        return is_users(self.get_object().author, self.request.user)


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    fields = ['content', 'latitude', 'longitude', 'header_image']
    template_name = 'blog/post_new.html'
    success_url = '/'

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.estado = dime_estado(form.instance.longitude, form.instance.latitude)
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['tag_line'] = 'Add a new post'
        return data


class PostUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Post
    fields = ['content', 'latitude', 'longitude', 'header_image']
    template_name = 'blog/post_new.html'
    success_url = '/'

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.estado = dime_estado(form.instance.longitude, form.instance.latitude)
        return super().form_valid(form)

    def test_func(self):
        return is_users(self.get_object().author, self.request.user)

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['tag_line'] = 'Edit a post'
        return data


class FollowsListView(ListView):
    model = Follow
    template_name = 'blog/follow.html'
    context_object_name = 'follows'

    def visible_user(self):
        return get_object_or_404(User, username=self.kwargs.get('username'))

    def get_queryset(self):
        user = self.visible_user()
        return Follow.objects.filter(user=user).order_by('-date')

    def get_context_data(self, *, object_list=None, **kwargs):
        data = super().get_context_data(**kwargs)
        data['follow'] = 'follows'
        return data


class FollowersListView(ListView):
    model = Follow
    template_name = 'blog/follow.html'
    context_object_name = 'follows'

    def visible_user(self):
        return get_object_or_404(User, username=self.kwargs.get('username'))

    def get_queryset(self):
        user = self.visible_user()
        return Follow.objects.filter(follow_user=user).order_by('-date')

    def get_context_data(self, *, object_list=None, **kwargs):
        data = super().get_context_data(**kwargs)
        data['follow'] = 'followers'
        return data


# Like Functionality====================================================================================

@login_required
def postpreference(request, postid, userpreference):
        
        if request.method == "POST":
                eachpost= get_object_or_404(Post, id=postid)

                obj=''

                valueobj=''

                try:
                        obj= Preference.objects.get(user= request.user, post= eachpost)

                        valueobj= obj.value #value of userpreference


                        valueobj= int(valueobj)

                        userpreference= int(userpreference)
                
                        if valueobj != userpreference:
                                obj.delete()


                                upref= Preference()
                                upref.user= request.user

                                upref.post= eachpost

                                upref.value= userpreference


                                if userpreference == 1 and valueobj != 1:
                                        eachpost.likes += 1
                                        eachpost.dislikes -=1
                                elif userpreference == 2 and valueobj != 2:
                                        eachpost.dislikes += 1
                                        eachpost.likes -= 1
                                

                                upref.save()

                                eachpost.save()
                        
                        
                                context= {'eachpost': eachpost,
                                  'postid': postid}

                                return redirect('blog-home')

                        elif valueobj == userpreference:
                                obj.delete()
                        
                                if userpreference == 1:
                                        eachpost.likes -= 1
                                elif userpreference == 2:
                                        eachpost.dislikes -= 1

                                eachpost.save()

                                context= {'eachpost': eachpost,
                                  'postid': postid}

                                return redirect('blog-home')
                                
                        
        
                
                except Preference.DoesNotExist:
                        upref= Preference()

                        upref.user= request.user

                        upref.post= eachpost

                        upref.value= userpreference

                        userpreference= int(userpreference)

                        if userpreference == 1:
                                eachpost.likes += 1
                        elif userpreference == 2:
                                eachpost.dislikes +=1

                        upref.save()

                        eachpost.save()                            


                        context= {'eachpost': eachpost,
                          'postid': postid}

                        return redirect('blog-home')


        else:
                eachpost= get_object_or_404(Post, id=postid)
                context= {'eachpost': eachpost,
                          'postid': postid}

                return redirect('blog-home')

# def traeHash():
#     for i in Post.objects.all():
#         publs = (str(i))
#         text = publs
#         hashes = re.findall('#(\w+)',text)
#         if hashes:
#             print(hashes)

# global hashes

def getHashTags(request):
    obj = 'piwipary'
    context = {
            'encontrar': obj,
        }
    return render(request,'blog/hashtags.html',context)
    
    # content = request.POST.get('busqueda')
    # if content == None:
    #     obj = 'si'
    #     context = {
    #         "encontrar":obj,
    #     }
    #     return render(request,'blog/hashtags.html',context)
    # elif content != '':
    #     obj = Post.objects.filter(content__contains=content)
    #     context = {
    #         "encontrar":obj,
    #     }
    #     return render(request,'blog/hashtags.html',context)
    # else:
    #     nada = 'Ingrese algún caractér en el cuadro de busquedas'
    #     also_nada = {
    #         'fnd': nada,
    #     }
    #     return render(request,'blog/hashtags.html', also_nada)

#busqueda de posts ==================================================================================>>
@login_required
def DataExtraction(request):

    # contenido = request.POST.get('busqueda')
    # usuario =  request.POST.get('username')
    # desde = request.POST.get('date1')
    # hasta = request.POST.get('date2')
    # prefijo = request.POST.get('estado')

    contenido = request.POST.get('sre')
    usuario =  request.POST.get('usr')
    desde = request.POST.get('from')
    hasta = request.POST.get('to')
    prefijo = request.POST.get('states')
    
    states = gdf['estado']
    provinces={
        'prov':states
    }

    if contenido==None and usuario==None and desde==None and hasta==None:
        return render(request,'blog/data_extraction.html',provinces)
    
    elif prefijo != '' and usuario == '' and desde == '' and hasta == '':
        obj = Post.objects.filter(estado__contains=prefijo)
        context = {
            'encontrar': obj,
            'prov': states,
        }
        return render(request,'blog/data_extraction.html', context)

    #cuando solo se llena el contenido
    elif contenido != '' and usuario == '' and desde == '' and hasta == '':
        obj = Post.objects.filter(content__contains=contenido)
        context = {
            'encontrar': obj,
            'prov': states,
        }
        return render(request,'blog/data_extraction.html', context)

    #cuando se llenan el contenido y las fechas unicamente
    elif contenido != '' and usuario == '' and desde != '' and hasta != '':
        obj = Post.objects.filter(content__contains=contenido, date_posted__range=[desde, hasta],)
        context = {
            'encontrar': obj,
            'prov': states,
        }
        return render(request,'blog/data_extraction.html', context) 
    
    #cuando se llenan las fechas unicamente
    elif contenido == '' and usuario == '' and desde != '' and hasta != '':
        obj = Post.objects.filter(date_posted__range=[desde, hasta],)
        context = {
            'encontrar': obj,
            'prov': states,
        }
        return render(request,'blog/data_extraction.html', context) 

    #cuando se llenan el contenido y el usuario unicamente
    elif contenido != '' and usuario != '' and desde == '' and hasta == '':
        obj = Post.objects.filter(content__contains=contenido, author__username__icontains=usuario,)
        context = {
            'encontrar': obj,
            'prov': states,
        }
        return render(request,'blog/data_extraction.html', context)        
        
    #cuando se llenan todos los campos
    elif contenido != '' and usuario != '' and desde != '' and hasta != '':
        obj = Post.objects.filter(content__contains=contenido, author__username__icontains=usuario, date_posted__range=[desde, hasta],)
        context = {
            'encontrar': obj,
            'prov': states,
        }
        return render(request,'blog/data_extraction.html', context)
    
    #cuando se llena el solo el campo usuario
    elif contenido == '' and usuario != '' and desde == '' and hasta == '':
        obj = Post.objects.filter(author__username__icontains=usuario,)
        context = {
            'encontrar': obj,
            'prov': states,
        }
        return render(request,'blog/data_extraction.html', context)
        
    else:
        nada = 'Ingrese algún caractér en el cuadro de busquedas'
        also_nada = {
            'fnd': nada,
            'prov': states,
        }
        return render(request,'blog/data_extraction.html', also_nada)

#fin de busqueda de posts ==================================================================================<<

class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]


class GroupViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [permissions.IsAuthenticated]



@api_view(['GET', 'POST', 'DELETE'])
def post_list(request):
    if request.method == 'GET':
        posts = Post.objects.all()
        
        title = request.query_params.get('title', None)
        if title is not None:
            posts = posts.filter(title__icontains=title)
        
        posts_serializer = PostSerializer(posts, many=True)
        return JsonResponse(posts_serializer.data, safe=False)
        # 'safe=False' for objects serialization
 
    elif request.method == 'POST':
        post_data = JSONParser().parse(request)
        post_serializer = PostSerializer(data=post_data)
        if post_serializer.is_valid():
            post_serializer.save()
            return JsonResponse(post_serializer.data, status=status.HTTP_201_CREATED) 
        return JsonResponse(post_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        count = Post.objects.all().delete()
        return JsonResponse({'message': '{} Posts were deleted successfully!'.format(count[0])}, status=status.HTTP_204_NO_CONTENT)
 