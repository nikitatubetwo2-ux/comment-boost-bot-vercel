"""
Анализатор YouTube каналов через YouTube Data API
"""

import re
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


@dataclass
class ChannelInfo:
    """Информация о канале"""
    channel_id: str
    title: str
    description: str
    subscriber_count: int
    video_count: int
    view_count: int
    thumbnail_url: str
    custom_url: str = ""
    country: str = ""
    published_at: str = ""  # Дата создания канала
    
    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class VideoInfo:
    """Информация о видео"""
    video_id: str
    title: str
    description: str
    thumbnail_url: str
    view_count: int
    like_count: int
    comment_count: int
    duration: str
    published_at: str
    tags: List[str]
    
    def to_dict(self) -> dict:
        return asdict(self)


class YouTubeAnalyzer:
    """Анализатор YouTube каналов и видео с ротацией ключей"""
    
    def __init__(self, api_keys: list = None, api_key: str = None):
        """
        api_keys: список ключей для ротации
        api_key: один ключ (для обратной совместимости)
        """
        if api_keys:
            self.api_keys = [k for k in api_keys if k]
        elif api_key:
            self.api_keys = [api_key]
        else:
            self.api_keys = []
        
        self.current_key_index = 0
        self._build_client()
    
    def _build_client(self):
        """Создание клиента с текущим ключом"""
        if self.api_keys:
            self.api_key = self.api_keys[self.current_key_index]
            self.youtube = build('youtube', 'v3', developerKey=self.api_key)
    
    def rotate_key(self):
        """Переключение на следующий ключ"""
        if len(self.api_keys) > 1:
            self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
            self._build_client()
            print(f"Переключение на YouTube ключ #{self.current_key_index + 1}")
    
    def extract_channel_id(self, url: str) -> Optional[str]:
        """Извлечение ID канала из URL"""
        patterns = [
            r'youtube\.com/channel/([a-zA-Z0-9_-]+)',
            r'youtube\.com/@([a-zA-Z0-9_-]+)',
            r'youtube\.com/c/([a-zA-Z0-9_-]+)',
            r'youtube\.com/user/([a-zA-Z0-9_-]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                identifier = match.group(1)
                # Если это @handle, нужно получить channel_id
                if '@' in url or '/c/' in url or '/user/' in url:
                    return self._resolve_channel_id(identifier, url)
                return identifier
        
        return None
    
    def _resolve_channel_id(self, identifier: str, url: str) -> Optional[str]:
        """Получение channel_id по handle или username с ротацией ключей"""
        for attempt in range(len(self.api_keys)):
            try:
                if '@' in url:
                    # Новый API для @handle (forHandle)
                    try:
                        response = self.youtube.channels().list(
                            part='id',
                            forHandle=identifier
                        ).execute()
                        if response.get('items'):
                            return response['items'][0]['id']
                    except HttpError as e:
                        if e.resp.status in [403, 429]:
                            print(f"Ключ #{self.current_key_index + 1} заблокирован, пробую следующий...")
                            self.rotate_key()
                            continue
                    
                    # Fallback: поиск по handle
                    response = self.youtube.search().list(
                        part='snippet',
                        q=f"@{identifier}",
                        type='channel',
                        maxResults=5
                    ).execute()
                    
                    # Ищем точное совпадение по customUrl
                    for item in response.get('items', []):
                        channel_id = item['id']['channelId']
                        ch_response = self.youtube.channels().list(
                            part='snippet',
                            id=channel_id
                        ).execute()
                        if ch_response.get('items'):
                            custom_url = ch_response['items'][0]['snippet'].get('customUrl', '')
                            if custom_url and identifier.lower() in custom_url.lower():
                                return channel_id
                    
                    # Если не нашли точное — берём первый результат
                    if response.get('items'):
                        return response['items'][0]['id']['channelId']
                else:
                    # Поиск по username
                    response = self.youtube.channels().list(
                        part='id',
                        forUsername=identifier
                    ).execute()
                    if response.get('items'):
                        return response['items'][0]['id']
                
                return None
            except HttpError as e:
                if e.resp.status in [403, 429]:
                    print(f"Ключ #{self.current_key_index + 1} заблокирован, пробую следующий...")
                    self.rotate_key()
                else:
                    print(f"Ошибка API: {e}")
                    return None
        return None
    
    def get_channel_info(self, channel_id: str) -> Optional[ChannelInfo]:
        """Получение информации о канале"""
        for attempt in range(len(self.api_keys)):
            try:
                response = self.youtube.channels().list(
                    part='snippet,statistics,brandingSettings',
                    id=channel_id
                ).execute()
                
                if not response.get('items'):
                    return None
                
                item = response['items'][0]
                snippet = item['snippet']
                stats = item['statistics']
                
                return ChannelInfo(
                    channel_id=channel_id,
                    title=snippet.get('title', ''),
                    description=snippet.get('description', ''),
                    subscriber_count=int(stats.get('subscriberCount', 0)),
                    video_count=int(stats.get('videoCount', 0)),
                    view_count=int(stats.get('viewCount', 0)),
                    thumbnail_url=snippet.get('thumbnails', {}).get('high', {}).get('url', ''),
                    custom_url=snippet.get('customUrl', ''),
                    country=snippet.get('country', ''),
                    published_at=snippet.get('publishedAt', '')
                )
            except HttpError as e:
                if e.resp.status in [403, 429]:
                    print(f"Квота исчерпана, переключаю ключ...")
                    self.rotate_key()
                else:
                    print(f"Ошибка получения канала: {e}")
                    break
        return None
    
    def get_channel_videos(self, channel_id: str, max_results: int = 50) -> List[VideoInfo]:
        """Получение списка видео канала"""
        videos = []
        
        for attempt in range(len(self.api_keys)):
            try:
                # Получаем uploads playlist
                channel_response = self.youtube.channels().list(
                    part='contentDetails',
                    id=channel_id
                ).execute()
                
                if not channel_response.get('items'):
                    return videos
                
                uploads_playlist = channel_response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
                
                # Получаем видео из плейлиста
                next_page = None
                while len(videos) < max_results:
                    playlist_response = self.youtube.playlistItems().list(
                        part='snippet',
                        playlistId=uploads_playlist,
                        maxResults=min(50, max_results - len(videos)),
                        pageToken=next_page
                    ).execute()
                    
                    video_ids = [item['snippet']['resourceId']['videoId'] 
                                for item in playlist_response.get('items', [])]
                    
                    if video_ids:
                        # Получаем детальную информацию о видео
                        videos_response = self.youtube.videos().list(
                            part='snippet,statistics,contentDetails',
                            id=','.join(video_ids)
                        ).execute()
                        
                        for item in videos_response.get('items', []):
                            snippet = item['snippet']
                            stats = item.get('statistics', {})
                            
                            videos.append(VideoInfo(
                                video_id=item['id'],
                                title=snippet.get('title', ''),
                                description=snippet.get('description', ''),
                                thumbnail_url=snippet.get('thumbnails', {}).get('maxres', 
                                             snippet.get('thumbnails', {}).get('high', {})).get('url', ''),
                                view_count=int(stats.get('viewCount', 0)),
                                like_count=int(stats.get('likeCount', 0)),
                                comment_count=int(stats.get('commentCount', 0)),
                                duration=item['contentDetails'].get('duration', ''),
                                published_at=snippet.get('publishedAt', ''),
                                tags=snippet.get('tags', [])
                            ))
                    
                    next_page = playlist_response.get('nextPageToken')
                    if not next_page:
                        break
                
                return videos
            except HttpError as e:
                if e.resp.status in [403, 429]:
                    print(f"Квота исчерпана при получении видео, переключаю ключ...")
                    self.rotate_key()
                else:
                    print(f"Ошибка получения видео: {e}")
                    break
        
        return videos
    
    def search_channels(self, query: str, max_results: int = 10, 
                        min_subscribers: int = 100,
                        exclude_shorts: bool = True) -> List[ChannelInfo]:
        """
        Поиск каналов по ключевым словам с ФИЛЬТРАЦИЕЙ
        
        Args:
            query: Поисковый запрос
            max_results: Максимум результатов
            min_subscribers: Минимум подписчиков (отсеивает мёртвые каналы)
            exclude_shorts: Исключать Shorts-каналы
        """
        channels = []
        
        for attempt in range(len(self.api_keys)):
            try:
                # Ищем больше каналов чтобы после фильтрации осталось достаточно
                response = self.youtube.search().list(
                    part='snippet',
                    q=query,
                    type='channel',
                    maxResults=min(50, max_results * 3)  # Берём с запасом для фильтрации
                ).execute()
                
                # Собираем channel_id
                channel_ids = [item['id']['channelId'] for item in response.get('items', [])]
                
                # Получаем инфо о всех каналах одним запросом
                if channel_ids:
                    channels_response = self.youtube.channels().list(
                        part='snippet,statistics',
                        id=','.join(channel_ids)
                    ).execute()
                    
                    for item in channels_response.get('items', []):
                        snippet = item['snippet']
                        stats = item['statistics']
                        
                        subs = int(stats.get('subscriberCount', 0))
                        
                        # ФИЛЬТР: минимум подписчиков
                        if subs < min_subscribers:
                            continue
                        
                        channel = ChannelInfo(
                            channel_id=item['id'],
                            title=snippet.get('title', ''),
                            description=snippet.get('description', ''),
                            subscriber_count=subs,
                            video_count=int(stats.get('videoCount', 0)),
                            view_count=int(stats.get('viewCount', 0)),
                            thumbnail_url=snippet.get('thumbnails', {}).get('high', {}).get('url', ''),
                            custom_url=snippet.get('customUrl', ''),
                            country=snippet.get('country', ''),
                            published_at=snippet.get('publishedAt', '')
                        )
                        
                        # ФИЛЬТР: исключаем Shorts-каналы
                        if exclude_shorts and self.is_shorts_channel(channel.channel_id):
                            print(f"Пропускаю Shorts-канал: {channel.title}")
                            continue
                        
                        channels.append(channel)
                        
                        # Достаточно результатов
                        if len(channels) >= max_results:
                            break
                
                # Сортируем по подписчикам (лучшие сверху)
                channels.sort(key=lambda x: x.subscriber_count, reverse=True)
                return channels[:max_results]
                
            except HttpError as e:
                if e.resp.status in [403, 429]:
                    print(f"Квота исчерпана, переключаю ключ...")
                    self.rotate_key()
                else:
                    print(f"Ошибка поиска: {e}")
                    break
        
        return channels
    
    def is_shorts_channel(self, channel_id: str) -> bool:
        """Проверка является ли канал Shorts-каналом"""
        try:
            videos = self.get_channel_videos(channel_id, max_results=10)
            if not videos:
                return False
            
            shorts_count = 0
            for video in videos:
                # Shorts обычно < 60 секунд
                duration = video.duration  # формат PT1M30S
                if duration:
                    # Парсим ISO 8601 duration
                    import re
                    match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration)
                    if match:
                        hours = int(match.group(1) or 0)
                        minutes = int(match.group(2) or 0)
                        seconds = int(match.group(3) or 0)
                        total_seconds = hours * 3600 + minutes * 60 + seconds
                        
                        if total_seconds <= 60:
                            shorts_count += 1
            
            # Если >70% видео - Shorts, это Shorts канал
            return shorts_count / len(videos) > 0.7
        except:
            return False
    
    def search_channels_by_videos(self, query: str, max_results: int = 10,
                                   min_subscribers: int = 100,
                                   exclude_shorts: bool = True) -> List[ChannelInfo]:
        """
        Поиск КАЧЕСТВЕННЫХ каналов через их видео
        
        Находит каналы с реальной активностью и хорошими показателями
        """
        channels = []
        seen_channel_ids = set()
        
        for attempt in range(len(self.api_keys)):
            try:
                all_channel_ids = []
                
                # Ищем видео по запросу - разные сортировки
                for order in ['viewCount', 'relevance', 'date']:
                    try:
                        response = self.youtube.search().list(
                            part='snippet',
                            q=query,
                            type='video',
                            maxResults=25,
                            order=order,
                            publishedAfter='2024-06-01T00:00:00Z',  # Только свежие видео (последние 6 мес)
                            videoDuration='medium'  # Исключаем Shorts (< 4 мин) и очень длинные
                        ).execute()
                        
                        for item in response.get('items', []):
                            channel_id = item['snippet']['channelId']
                            if channel_id not in seen_channel_ids:
                                seen_channel_ids.add(channel_id)
                                all_channel_ids.append(channel_id)
                    except:
                        continue
                
                # Получаем инфо о каналах
                if all_channel_ids:
                    # Берём порциями по 50 (лимит API)
                    for i in range(0, len(all_channel_ids), 50):
                        batch = all_channel_ids[i:i+50]
                        
                        channels_response = self.youtube.channels().list(
                            part='snippet,statistics',
                            id=','.join(batch)
                        ).execute()
                        
                        for item in channels_response.get('items', []):
                            snippet = item['snippet']
                            stats = item['statistics']
                            
                            subs = int(stats.get('subscriberCount', 0))
                            views = int(stats.get('viewCount', 0))
                            videos = int(stats.get('videoCount', 0))
                            
                            # ФИЛЬТРЫ КАЧЕСТВА:
                            # 1. Минимум подписчиков
                            if subs < min_subscribers:
                                continue
                            
                            # 2. Должны быть видео
                            if videos < 5:
                                continue
                            
                            # 3. Хорошее соотношение просмотров к подписчикам
                            if views < subs * 5:  # Минимум 5 просмотров на подписчика
                                continue
                            
                            channel = ChannelInfo(
                                channel_id=item['id'],
                                title=snippet.get('title', ''),
                                description=snippet.get('description', ''),
                                subscriber_count=subs,
                                video_count=videos,
                                view_count=views,
                                thumbnail_url=snippet.get('thumbnails', {}).get('high', {}).get('url', ''),
                                custom_url=snippet.get('customUrl', ''),
                                country=snippet.get('country', ''),
                                published_at=snippet.get('publishedAt', '')
                            )
                            
                            # ФИЛЬТР: исключаем Shorts-каналы
                            if exclude_shorts and self.is_shorts_channel(channel.channel_id):
                                print(f"Пропускаю Shorts-канал: {channel.title}")
                                continue
                            
                            channels.append(channel)
                
                # Сортируем по "качеству" (подписчики * engagement)
                for ch in channels:
                    ch._score = ch.subscriber_count * (ch.view_count / max(ch.video_count, 1))
                
                channels.sort(key=lambda x: getattr(x, '_score', 0), reverse=True)
                return channels[:max_results]
                
            except HttpError as e:
                if e.resp.status in [403, 429]:
                    print(f"Квота исчерпана, переключаю ключ...")
                    self.rotate_key()
                else:
                    print(f"Ошибка поиска по видео: {e}")
                    break
        
        return channels
    
    def hunt_fresh_stars(self, niche: str, max_results: int = 20,
                         max_first_video_days: int = 60,
                         language: str = "ru") -> List[ChannelInfo]:
        """
        🎯 ОХОТНИК ЗА СВЕЖИМИ ЗВЁЗДАМИ
        
        Ищет каналы где ПЕРВОЕ ВИДЕО выложено не более X дней назад,
        но уже есть хорошие показатели.
        
        Логика:
        1. Ищем свежие видео в нише (последние 60 дней)
        2. Для каждого канала проверяем дату ПЕРВОГО видео
        3. Если первое видео < 60 дней — это свежий канал
        4. Оцениваем показатели и ранжируем
        
        Args:
            niche: Ниша для поиска (например "военная история")
            max_results: Максимум результатов
            max_first_video_days: Максимум дней с первого видео (по умолчанию 60)
            language: Код языка для фильтрации (ru, en, es, de, fr, pt, it)
        """
        from datetime import datetime, timedelta
        
        fresh_stars = []
        seen_ids = set()
        cutoff_date = datetime.now() - timedelta(days=max_first_video_days)
        
        # Маппинг языка на регион для лучших результатов
        lang_to_region = {
            "ru": "RU", "en": "US", "es": "ES", "de": "DE",
            "fr": "FR", "pt": "BR", "it": "IT"
        }
        region = lang_to_region.get(language, "US")
        
        print(f"🎯 Охота за свежими звёздами в нише: {niche} ({language.upper()})")
        print(f"   Ищем каналы с первым видео после: {cutoff_date.strftime('%Y-%m-%d')}")
        
        for attempt in range(len(self.api_keys)):
            try:
                # Ищем свежие видео в нише с фильтром по языку
                response = self.youtube.search().list(
                    part='snippet',
                    q=niche,
                    type='video',
                    maxResults=50,
                    order='date',  # Сначала самые свежие
                    publishedAfter=(datetime.now() - timedelta(days=90)).strftime('%Y-%m-%dT00:00:00Z'),
                    videoDuration='medium',  # Исключаем Shorts
                    relevanceLanguage=language,  # Фильтр по языку контента
                    regionCode=region  # Регион для лучшей релевантности
                ).execute()
                
                # Собираем уникальные channel_id
                channel_ids = []
                for item in response.get('items', []):
                    cid = item['snippet']['channelId']
                    if cid not in seen_ids:
                        seen_ids.add(cid)
                        channel_ids.append(cid)
                
                print(f"   Найдено {len(channel_ids)} уникальных каналов, проверяю...")
                
                # Проверяем каждый канал
                for cid in channel_ids:
                    if len(fresh_stars) >= max_results:
                        break
                    
                    try:
                        # Получаем инфо о канале
                        ch_response = self.youtube.channels().list(
                            part='snippet,statistics,contentDetails',
                            id=cid
                        ).execute()
                        
                        if not ch_response.get('items'):
                            continue
                        
                        ch_item = ch_response['items'][0]
                        snippet = ch_item['snippet']
                        stats = ch_item['statistics']
                        
                        subs = int(stats.get('subscriberCount', 0))
                        views = int(stats.get('viewCount', 0))
                        videos = int(stats.get('videoCount', 0))
                        
                        if videos < 3:  # Минимум 3 видео
                            continue
                        
                        # Получаем дату ПЕРВОГО видео
                        uploads_playlist = ch_item['contentDetails']['relatedPlaylists']['uploads']
                        
                        # Получаем последнюю страницу плейлиста (там первое видео)
                        first_video_date = self._get_first_video_date(uploads_playlist)
                        
                        if not first_video_date:
                            continue
                        
                        # Проверяем что первое видео свежее
                        days_since_first = (datetime.now(first_video_date.tzinfo) - first_video_date).days
                        
                        if days_since_first > max_first_video_days:
                            continue  # Канал слишком старый
                        
                        # Считаем метрики
                        avg_views = views / videos
                        virality = avg_views / max(subs, 1)
                        
                        # Определяем тип звезды
                        star_type = ""
                        score = 0
                        
                        if subs < 500 and avg_views > 5000:
                            star_type = f"🔥 БОМБА! {subs} subs, {int(avg_views/1000)}K/vid за {days_since_first}д"
                            score = 1000
                        elif subs < 1000 and avg_views > 3000:
                            star_type = f"⭐ Взлёт! {int(avg_views/1000)}K/vid, {days_since_first}д"
                            score = 800
                        elif subs < 2000 and virality > 10:
                            star_type = f"📈 Рост x{int(virality)}, {days_since_first}д"
                            score = 600
                        elif days_since_first < 30 and avg_views > 1000:
                            star_type = f"🆕 Новичок {days_since_first}д, {int(avg_views/1000)}K/vid"
                            score = 400
                        else:
                            continue  # Не подходит
                        
                        channel = ChannelInfo(
                            channel_id=cid,
                            title=snippet.get('title', ''),
                            description=snippet.get('description', ''),
                            subscriber_count=subs,
                            video_count=videos,
                            view_count=views,
                            thumbnail_url=snippet.get('thumbnails', {}).get('high', {}).get('url', ''),
                            custom_url=snippet.get('customUrl', ''),
                            country=snippet.get('country', ''),
                            published_at=snippet.get('publishedAt', '')
                        )
                        
                        # Метаданные
                        channel._star_type = star_type
                        channel._score = score
                        channel._virality = virality
                        channel._avg_views = avg_views
                        channel._days_since_first = days_since_first
                        channel._first_video_date = first_video_date.strftime('%Y-%m-%d')
                        
                        fresh_stars.append(channel)
                        print(f"   ✅ {channel.title}: {star_type}")
                        
                    except Exception as e:
                        continue
                
                # Сортируем по score
                fresh_stars.sort(key=lambda x: getattr(x, '_score', 0), reverse=True)
                return fresh_stars[:max_results]
                
            except HttpError as e:
                if e.resp.status in [403, 429]:
                    self.rotate_key()
                else:
                    print(f"Ошибка: {e}")
                    break
        
        return fresh_stars
    
    def _get_first_video_date(self, uploads_playlist: str):
        """Получить дату первого видео канала"""
        from datetime import datetime
        
        try:
            # Получаем общее количество видео
            response = self.youtube.playlistItems().list(
                part='snippet',
                playlistId=uploads_playlist,
                maxResults=1
            ).execute()
            
            total = response.get('pageInfo', {}).get('totalResults', 0)
            if total == 0:
                return None
            
            # Идём к последней странице (там первое видео)
            # YouTube API не даёт прямой доступ, поэтому берём последние видео
            # и ищем самое старое
            
            all_dates = []
            next_page = None
            pages_checked = 0
            
            while pages_checked < 10:  # Максимум 10 страниц (500 видео)
                response = self.youtube.playlistItems().list(
                    part='snippet',
                    playlistId=uploads_playlist,
                    maxResults=50,
                    pageToken=next_page
                ).execute()
                
                for item in response.get('items', []):
                    pub = item['snippet'].get('publishedAt')
                    if pub:
                        try:
                            dt = datetime.fromisoformat(pub.replace('Z', '+00:00'))
                            all_dates.append(dt)
                        except:
                            pass
                
                next_page = response.get('nextPageToken')
                if not next_page:
                    break
                pages_checked += 1
            
            if all_dates:
                return min(all_dates)  # Самая ранняя дата = первое видео
            
            return None
            
        except Exception as e:
            return None
    
    def find_rising_stars(self, query: str, max_results: int = 15,
                          max_age_months: int = 6) -> List[ChannelInfo]:
        """
        Поиск "восходящих звёзд" — каналов с АНОМАЛЬНО высокими просмотрами
        
        Ищем каналы где просмотры >> подписчиков (признак вирусности)
        Например: 500 подписчиков но 30-40к просмотров на видео = ЗОЛОТО!
        
        Args:
            query: Поисковый запрос
            max_results: Максимум результатов
            max_age_months: Максимальный возраст канала в месяцах
        """
        from datetime import datetime, timedelta
        
        min_created_date = datetime.now() - timedelta(days=max_age_months * 30)
        
        # Ищем через свежие видео с высокими просмотрами
        rising_stars = []
        seen_ids = set()
        
        for attempt in range(len(self.api_keys)):
            try:
                # Ищем видео с высокими просмотрами за последние месяцы
                for order in ['viewCount', 'date']:
                    response = self.youtube.search().list(
                        part='snippet',
                        q=query,
                        type='video',
                        maxResults=50,
                        order=order,
                        publishedAfter=(datetime.now() - timedelta(days=90)).strftime('%Y-%m-%dT00:00:00Z'),
                        videoDuration='medium'  # Исключаем Shorts
                    ).execute()
                    
                    # Собираем channel_id
                    channel_ids = []
                    for item in response.get('items', []):
                        cid = item['snippet']['channelId']
                        if cid not in seen_ids:
                            seen_ids.add(cid)
                            channel_ids.append(cid)
                    
                    if not channel_ids:
                        continue
                    
                    # Получаем инфо о каналах
                    for i in range(0, len(channel_ids), 50):
                        batch = channel_ids[i:i+50]
                        channels_response = self.youtube.channels().list(
                            part='snippet,statistics',
                            id=','.join(batch)
                        ).execute()
                        
                        for item in channels_response.get('items', []):
                            snippet = item['snippet']
                            stats = item['statistics']
                            
                            subs = int(stats.get('subscriberCount', 0))
                            views = int(stats.get('viewCount', 0))
                            videos = int(stats.get('videoCount', 0))
                            
                            if videos == 0:
                                continue
                            
                            avg_views = views / videos
                            
                            # КЛЮЧЕВАЯ МЕТРИКА: соотношение просмотров к подписчикам
                            # Если avg_views > subs * 10 — это АНОМАЛИЯ (вирусность!)
                            virality_score = avg_views / max(subs, 1)
                            
                            # Фильтр Shorts
                            title = snippet.get('title', '').lower()
                            if 'shorts' in title or 'short' in title:
                                continue
                            
                            # Проверяем возраст канала
                            pub_date = snippet.get('publishedAt', '')
                            age_days = 9999
                            if pub_date:
                                try:
                                    created = datetime.fromisoformat(pub_date.replace('Z', '+00:00'))
                                    age_days = (datetime.now(created.tzinfo) - created).days
                                except:
                                    pass
                            
                            # Категоризация по "золотости"
                            is_gold = False
                            star_type = ""
                            
                            # ЗОЛОТО: мало подписчиков но много просмотров
                            if subs < 1000 and avg_views > 10000:
                                is_gold = True
                                star_type = f"🔥 ЗОЛОТО! {subs} subs, {int(avg_views/1000)}K views/vid"
                            elif subs < 5000 and avg_views > 20000:
                                is_gold = True
                                star_type = f"⭐ Растущий: {int(avg_views/1000)}K views/vid"
                            elif subs < 10000 and virality_score > 20:
                                is_gold = True
                                star_type = f"📈 Вирусный: x{int(virality_score)} views/subs"
                            elif age_days < 90 and avg_views > 5000:
                                is_gold = True
                                star_type = f"🆕 Новичок {age_days}д: {int(avg_views/1000)}K/vid"
                            elif virality_score > 50:
                                is_gold = True
                                star_type = f"💎 Аномалия: x{int(virality_score)}"
                            
                            if is_gold:
                                channel = ChannelInfo(
                                    channel_id=item['id'],
                                    title=snippet.get('title', ''),
                                    description=snippet.get('description', ''),
                                    subscriber_count=subs,
                                    video_count=videos,
                                    view_count=views,
                                    thumbnail_url=snippet.get('thumbnails', {}).get('high', {}).get('url', ''),
                                    custom_url=snippet.get('customUrl', ''),
                                    country=snippet.get('country', ''),
                                    published_at=pub_date
                                )
                                # Добавляем метаданные
                                channel._star_type = star_type
                                channel._virality = virality_score
                                channel._avg_views = avg_views
                                channel._age_days = age_days
                                rising_stars.append(channel)
                
                # Сортируем по вирусности (просмотры/подписчики)
                rising_stars.sort(key=lambda x: getattr(x, '_virality', 0), reverse=True)
                return rising_stars[:max_results]
                
            except HttpError as e:
                if e.resp.status in [403, 429]:
                    self.rotate_key()
                else:
                    print(f"Ошибка поиска восходящих звёзд: {e}")
                    break
        
        return rising_stars[:max_results]
    
    def get_video_details(self, video_id: str) -> Optional[VideoInfo]:
        """Получение детальной информации о видео"""
        try:
            response = self.youtube.videos().list(
                part='snippet,statistics,contentDetails',
                id=video_id
            ).execute()
            
            if not response.get('items'):
                return None
            
            item = response['items'][0]
            snippet = item['snippet']
            stats = item.get('statistics', {})
            
            return VideoInfo(
                video_id=video_id,
                title=snippet.get('title', ''),
                description=snippet.get('description', ''),
                thumbnail_url=snippet.get('thumbnails', {}).get('maxres', 
                             snippet.get('thumbnails', {}).get('high', {})).get('url', ''),
                view_count=int(stats.get('viewCount', 0)),
                like_count=int(stats.get('likeCount', 0)),
                comment_count=int(stats.get('commentCount', 0)),
                duration=item['contentDetails'].get('duration', ''),
                published_at=snippet.get('publishedAt', ''),
                tags=snippet.get('tags', [])
            )
        except HttpError as e:
            print(f"Ошибка получения видео: {e}")
            return None
    
    def analyze_channel_stats(self, videos: List[VideoInfo]) -> Dict[str, Any]:
        """Анализ статистики канала"""
        if not videos:
            return {}
        
        total_views = sum(v.view_count for v in videos)
        total_likes = sum(v.like_count for v in videos)
        total_comments = sum(v.comment_count for v in videos)
        
        avg_views = total_views // len(videos)
        avg_likes = total_likes // len(videos)
        avg_comments = total_comments // len(videos)
        
        # Топ видео по просмотрам
        top_videos = sorted(videos, key=lambda x: x.view_count, reverse=True)[:10]
        
        # Собираем все теги
        all_tags = []
        for v in videos:
            all_tags.extend(v.tags)
        
        # Частотность тегов
        tag_freq = {}
        for tag in all_tags:
            tag_freq[tag] = tag_freq.get(tag, 0) + 1
        
        top_tags = sorted(tag_freq.items(), key=lambda x: x[1], reverse=True)[:20]
        
        return {
            'total_videos': len(videos),
            'total_views': total_views,
            'total_likes': total_likes,
            'total_comments': total_comments,
            'avg_views': avg_views,
            'avg_likes': avg_likes,
            'avg_comments': avg_comments,
            'engagement_rate': round((avg_likes + avg_comments) / max(avg_views, 1) * 100, 2),
            'top_videos': [v.to_dict() for v in top_videos],
            'top_tags': top_tags
        }
