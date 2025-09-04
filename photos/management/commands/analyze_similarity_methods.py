from django.core.management.base import BaseCommand
from photos.models import Photo, PhotoSimilarity
from photos.utils import (
    find_similar_photos_cached,
    calculate_similarity,
    calculate_pearson_similarity,
    calculate_exif_similarity,
    calculate_hybrid_similarity
)
import time
import statistics


class Command(BaseCommand):
    help = 'Analyze all similarity methods and provide recommendations'

    def add_arguments(self, parser):
        parser.add_argument(
            '--photo-count',
            type=int,
            default=10,
            help='Number of photos to test (default: 10)',
        )
        parser.add_argument(
            '--threshold',
            type=float,
            default=0.5,
            help='Similarity threshold (default: 0.5)',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=10,
            help='Maximum results per photo (default: 10)',
        )

    def handle(self, *args, **options):
        # Get photos with embeddings
        photos_with_embeddings = Photo.objects.exclude(
            embedding__isnull=True
        ).exclude(
            embedding=[]
        )
        
        if not photos_with_embeddings.exists():
            self.stdout.write(
                self.style.ERROR('No photos with embeddings found. Please generate embeddings first.')
            )
            return
        
        # Select test photos
        test_photos = photos_with_embeddings[:options['photo_count']]
        threshold = options['threshold']
        limit = options['limit']
        
        self.stdout.write(f"Analyzing {len(test_photos)} photos...")
        self.stdout.write(f"Parameters: threshold={threshold}, limit={limit}")
        
        # Test all methods
        methods = {
            'hybrid_cosine': 'Hybrid Cosine',
            'hybrid_pearson': 'Hybrid Pearson',
            'visual_cosine': 'Visual Only (Cosine)',
            'visual_pearson': 'Visual Only (Pearson)',
            'exif_cosine': 'EXIF Only (Cosine)',
            'exif_pearson': 'EXIF Only (Pearson)',
        }
        
        results = {method: {'times': [], 'counts': [], 'scores': []} for method in methods.keys()}
        
        for i, photo in enumerate(test_photos, 1):
            self.stdout.write(f"\nTesting photo {i}/{len(test_photos)}: {photo.title} (ID: {photo.id})")
            
            # Test each method
            for method_key, method_name in methods.items():
                start_time = time.time()
                
                try:
                    if method_key == 'hybrid_cosine':
                        similar_results = find_similar_photos_cached(
                            photo, limit=limit, threshold=threshold, method="cosine", use_cache=True
                        )
                    elif method_key == 'hybrid_pearson':
                        similar_results = find_similar_photos_cached(
                            photo, limit=limit, threshold=threshold, method="pearson", use_cache=True
                        )
                    elif method_key == 'visual_cosine':
                        similar_results = []
                        for other_photo in photos_with_embeddings.exclude(id=photo.id):
                            try:
                                visual_sim = calculate_similarity(photo.embedding, other_photo.embedding)
                                if visual_sim >= threshold:
                                    similar_results.append({
                                        'photo': other_photo,
                                        'similarity': visual_sim,
                                        'visual': visual_sim,
                                        'exif': 0.0,
                                        'final': visual_sim
                                    })
                            except Exception:
                                continue
                        similar_results.sort(key=lambda x: x['similarity'], reverse=True)
                        similar_results = similar_results[:limit]
                    elif method_key == 'visual_pearson':
                        similar_results = []
                        for other_photo in photos_with_embeddings.exclude(id=photo.id):
                            try:
                                visual_sim = calculate_pearson_similarity(photo.embedding, other_photo.embedding)
                                if visual_sim >= threshold:
                                    similar_results.append({
                                        'photo': other_photo,
                                        'similarity': visual_sim,
                                        'visual': visual_sim,
                                        'exif': 0.0,
                                        'final': visual_sim
                                    })
                            except Exception:
                                continue
                        similar_results.sort(key=lambda x: x['similarity'], reverse=True)
                        similar_results = similar_results[:limit]
                    elif method_key == 'exif_cosine':
                        similar_results = []
                        for other_photo in photos_with_embeddings.exclude(id=photo.id):
                            try:
                                exif_sim = calculate_exif_similarity(photo, other_photo, method="cosine")
                                if exif_sim >= threshold:
                                    similar_results.append({
                                        'photo': other_photo,
                                        'similarity': exif_sim,
                                        'visual': 0.0,
                                        'exif': exif_sim,
                                        'final': exif_sim
                                    })
                            except Exception:
                                continue
                        similar_results.sort(key=lambda x: x['similarity'], reverse=True)
                        similar_results = similar_results[:limit]
                    elif method_key == 'exif_pearson':
                        similar_results = []
                        for other_photo in photos_with_embeddings.exclude(id=photo.id):
                            try:
                                exif_sim = calculate_exif_similarity(photo, other_photo, method="pearson")
                                if exif_sim >= threshold:
                                    similar_results.append({
                                        'photo': other_photo,
                                        'similarity': exif_sim,
                                        'visual': 0.0,
                                        'exif': exif_sim,
                                        'final': exif_sim
                                    })
                            except Exception:
                                continue
                        similar_results.sort(key=lambda x: x['similarity'], reverse=True)
                        similar_results = similar_results[:limit]
                    
                    elapsed_time = time.time() - start_time
                    result_count = len(similar_results)
                    avg_score = statistics.mean([r['final'] for r in similar_results]) if similar_results else 0
                    
                    results[method_key]['times'].append(elapsed_time)
                    results[method_key]['counts'].append(result_count)
                    results[method_key]['scores'].append(avg_score)
                    
                except Exception as e:
                    self.stdout.write(f"  Error with {method_name}: {e}")
                    results[method_key]['times'].append(0)
                    results[method_key]['counts'].append(0)
                    results[method_key]['scores'].append(0)
        
        # Analyze results
        self.stdout.write(f"\n{'='*80}")
        self.stdout.write(f"ANALYSIS RESULTS")
        self.stdout.write(f"{'='*80}")
        
        analysis = {}
        
        for method_key, method_name in methods.items():
            times = results[method_key]['times']
            counts = results[method_key]['counts']
            scores = results[method_key]['scores']
            
            avg_time = statistics.mean(times)
            avg_count = statistics.mean(counts)
            avg_score = statistics.mean(scores)
            
            analysis[method_key] = {
                'name': method_name,
                'avg_time': avg_time,
                'avg_count': avg_count,
                'avg_score': avg_score,
                'total_time': sum(times)
            }
            
            self.stdout.write(f"\n{method_name}:")
            self.stdout.write(f"  - Average time: {avg_time:.3f}s")
            self.stdout.write(f"  - Average results: {avg_count:.1f}")
            self.stdout.write(f"  - Average score: {avg_score:.3f}")
            self.stdout.write(f"  - Total time: {sum(times):.3f}s")
        
        # Recommendations
        self.stdout.write(f"\n{'='*80}")
        self.stdout.write(f"RECOMMENDATIONS")
        self.stdout.write(f"{'='*80}")
        
        # Speed ranking
        speed_ranking = sorted(analysis.items(), key=lambda x: x[1]['avg_time'])
        self.stdout.write(f"\n🏃 SPEED RANKING (fastest to slowest):")
        for i, (method_key, data) in enumerate(speed_ranking, 1):
            self.stdout.write(f"  {i}. {data['name']}: {data['avg_time']:.3f}s")
        
        # Quality ranking (based on average score)
        quality_ranking = sorted(analysis.items(), key=lambda x: x[1]['avg_score'], reverse=True)
        self.stdout.write(f"\n🎯 QUALITY RANKING (highest to lowest average score):")
        for i, (method_key, data) in enumerate(quality_ranking, 1):
            self.stdout.write(f"  {i}. {data['name']}: {data['avg_score']:.3f}")
        
        # Results count ranking
        count_ranking = sorted(analysis.items(), key=lambda x: x[1]['avg_count'], reverse=True)
        self.stdout.write(f"\n📊 RESULTS COUNT RANKING (most to least results):")
        for i, (method_key, data) in enumerate(count_ranking, 1):
            self.stdout.write(f"  {i}. {data['name']}: {data['avg_count']:.1f} results")
        
        # Overall recommendation
        self.stdout.write(f"\n{'='*80}")
        self.stdout.write(f"FINAL RECOMMENDATION")
        self.stdout.write(f"{'='*80}")
        
        # Calculate composite score (normalized)
        max_time = max(data['avg_time'] for data in analysis.values())
        max_score = max(data['avg_score'] for data in analysis.values())
        max_count = max(data['avg_count'] for data in analysis.values())
        
        composite_scores = {}
        for method_key, data in analysis.items():
            # Normalize and weight: 40% quality, 30% speed, 30% results count
            quality_norm = data['avg_score'] / max_score if max_score > 0 else 0
            speed_norm = 1 - (data['avg_time'] / max_time) if max_time > 0 else 0
            count_norm = data['avg_count'] / max_count if max_count > 0 else 0
            
            composite_score = (0.4 * quality_norm) + (0.3 * speed_norm) + (0.3 * count_norm)
            composite_scores[method_key] = composite_score
        
        best_method = max(composite_scores.items(), key=lambda x: x[1])
        best_data = analysis[best_method[0]]
        
        self.stdout.write(f"\n🏆 BEST OVERALL METHOD: {best_data['name']}")
        self.stdout.write(f"   Composite Score: {best_method[1]:.3f}")
        self.stdout.write(f"   Average Time: {best_data['avg_time']:.3f}s")
        self.stdout.write(f"   Average Score: {best_data['avg_score']:.3f}")
        self.stdout.write(f"   Average Results: {best_data['avg_count']:.1f}")
        
        # Specific recommendations
        self.stdout.write(f"\n📋 SPECIFIC RECOMMENDATIONS:")
        
        fastest = speed_ranking[0]
        self.stdout.write(f"   ⚡ Fastest: {fastest[1]['name']} ({fastest[1]['avg_time']:.3f}s)")
        
        highest_quality = quality_ranking[0]
        self.stdout.write(f"   🎯 Highest Quality: {highest_quality[1]['name']} ({highest_quality[1]['avg_score']:.3f})")
        
        most_results = count_ranking[0]
        self.stdout.write(f"   📊 Most Results: {most_results[1]['name']} ({most_results[1]['avg_count']:.1f} results)")
        
        # Use case recommendations
        self.stdout.write(f"\n🎯 USE CASE RECOMMENDATIONS:")
        self.stdout.write(f"   🔍 Finding duplicates: {quality_ranking[0][1]['name']} (highest precision)")
        self.stdout.write(f"   ⚡ Real-time search: {speed_ranking[0][1]['name']} (fastest)")
        self.stdout.write(f"   📱 General recommendations: {best_data['name']} (best balance)")
        self.stdout.write(f"   🎨 Style-based search: Visual Only methods")
        self.stdout.write(f"   📷 Metadata-based search: EXIF Only methods")
        
        self.stdout.write(f"\n{self.style.SUCCESS('Analysis completed successfully!')}")
