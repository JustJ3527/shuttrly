from django.core.management.base import BaseCommand
from photos.models import Photo
from photos.utils import calculate_exif_similarity
import statistics


class Command(BaseCommand):
    help = 'Analyze EXIF similarity scores to understand the distribution'

    def add_arguments(self, parser):
        parser.add_argument(
            '--photo-count',
            type=int,
            default=20,
            help='Number of photos to analyze (default: 20)',
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
                self.style.ERROR('No photos with embeddings found.')
            )
            return
        
        # Select test photos
        test_photos = photos_with_embeddings[:options['photo_count']]
        
        self.stdout.write(f"Analyzing EXIF similarity for {len(test_photos)} photos...")
        
        # Calculate all pairwise EXIF similarities
        exif_scores = []
        detailed_results = []
        
        for i, photo1 in enumerate(test_photos):
            for j, photo2 in enumerate(test_photos):
                if i < j:  # Avoid duplicates and self-comparison
                    try:
                        exif_sim = calculate_exif_similarity(photo1, photo2)
                        exif_scores.append(exif_sim)
                        
                        detailed_results.append({
                            'photo1_id': photo1.id,
                            'photo1_title': photo1.title,
                            'photo2_id': photo2.id,
                            'photo2_title': photo2.title,
                            'exif_sim': exif_sim,
                            'photo1_camera': f"{photo1.camera_make} {photo1.camera_model}",
                            'photo2_camera': f"{photo2.camera_make} {photo2.camera_model}",
                            'photo1_date': photo1.date_taken,
                            'photo2_date': photo2.date_taken,
                            'photo1_iso': photo1.iso,
                            'photo2_iso': photo2.iso,
                            'photo1_aperture': photo1.aperture,
                            'photo2_aperture': photo2.aperture,
                        })
                    except Exception as e:
                        self.stdout.write(f"Error comparing photos {photo1.id} and {photo2.id}: {e}")
        
        if not exif_scores:
            self.stdout.write(self.style.ERROR('No EXIF similarities calculated.'))
            return
        
        # Analyze the distribution
        self.stdout.write(f"\n{'='*80}")
        self.stdout.write(f"EXIF SIMILARITY ANALYSIS")
        self.stdout.write(f"{'='*80}")
        
        self.stdout.write(f"\nTotal comparisons: {len(exif_scores)}")
        self.stdout.write(f"Mean EXIF similarity: {statistics.mean(exif_scores):.3f}")
        self.stdout.write(f"Median EXIF similarity: {statistics.median(exif_scores):.3f}")
        self.stdout.write(f"Min EXIF similarity: {min(exif_scores):.3f}")
        self.stdout.write(f"Max EXIF similarity: {max(exif_scores):.3f}")
        self.stdout.write(f"Standard deviation: {statistics.stdev(exif_scores):.3f}")
        
        # Distribution analysis
        score_ranges = [
            (0.0, 0.1, "Very Low (0.0-0.1)"),
            (0.1, 0.3, "Low (0.1-0.3)"),
            (0.3, 0.5, "Medium (0.3-0.5)"),
            (0.5, 0.7, "High (0.5-0.7)"),
            (0.7, 0.9, "Very High (0.7-0.9)"),
            (0.9, 1.0, "Identical (0.9-1.0)"),
        ]
        
        self.stdout.write(f"\n📊 DISTRIBUTION ANALYSIS:")
        for min_val, max_val, label in score_ranges:
            count = sum(1 for score in exif_scores if min_val <= score < max_val)
            percentage = (count / len(exif_scores)) * 100
            self.stdout.write(f"  {label}: {count} comparisons ({percentage:.1f}%)")
        
        # Show some examples
        self.stdout.write(f"\n🔍 EXAMPLE COMPARISONS:")
        
        # Sort by similarity score
        detailed_results.sort(key=lambda x: x['exif_sim'], reverse=True)
        
        # Show highest similarities
        self.stdout.write(f"\nHighest EXIF similarities:")
        for result in detailed_results[:5]:
            self.stdout.write(f"  {result['exif_sim']:.3f}: Photo {result['photo1_id']} vs Photo {result['photo2_id']}")
            self.stdout.write(f"    Camera: {result['photo1_camera']} vs {result['photo2_camera']}")
            self.stdout.write(f"    Date: {result['photo1_date']} vs {result['photo2_date']}")
            self.stdout.write(f"    ISO: {result['photo1_iso']} vs {result['photo2_iso']}")
            self.stdout.write(f"    Aperture: {result['photo1_aperture']} vs {result['photo2_aperture']}")
            self.stdout.write()
        
        # Show lowest similarities
        self.stdout.write(f"Lowest EXIF similarities:")
        for result in detailed_results[-5:]:
            self.stdout.write(f"  {result['exif_sim']:.3f}: Photo {result['photo1_id']} vs Photo {result['photo2_id']}")
            self.stdout.write(f"    Camera: {result['photo1_camera']} vs {result['photo2_camera']}")
            self.stdout.write(f"    Date: {result['photo1_date']} vs {result['photo2_date']}")
            self.stdout.write(f"    ISO: {result['photo1_iso']} vs {result['photo2_iso']}")
            self.stdout.write(f"    Aperture: {result['photo1_aperture']} vs {result['photo2_aperture']}")
            self.stdout.write()
        
        # Camera analysis
        self.stdout.write(f"\n📷 CAMERA ANALYSIS:")
        cameras = {}
        for result in detailed_results:
            camera1 = result['photo1_camera']
            camera2 = result['photo2_camera']
            
            if camera1 not in cameras:
                cameras[camera1] = {'count': 0, 'scores': []}
            if camera2 not in cameras:
                cameras[camera2] = {'count': 0, 'scores': []}
            
            cameras[camera1]['count'] += 1
            cameras[camera1]['scores'].append(result['exif_sim'])
            cameras[camera2]['count'] += 1
            cameras[camera2]['scores'].append(result['exif_sim'])
        
        for camera, data in sorted(cameras.items(), key=lambda x: x[1]['count'], reverse=True):
            avg_score = statistics.mean(data['scores']) if data['scores'] else 0
            self.stdout.write(f"  {camera}: {data['count']} comparisons, avg similarity: {avg_score:.3f}")
        
        # Recommendations
        self.stdout.write(f"\n💡 RECOMMENDATIONS:")
        
        if max(exif_scores) > 0.9:
            self.stdout.write("  ✅ High EXIF similarities found - good for duplicate detection")
        else:
            self.stdout.write("  ⚠️  No very high EXIF similarities - limited duplicate detection")
        
        if statistics.mean(exif_scores) < 0.3:
            self.stdout.write("  📊 Low average EXIF similarity - photos are quite diverse")
        else:
            self.stdout.write("  📊 Moderate average EXIF similarity - some common patterns")
        
        if len(set(exif_scores)) < 10:
            self.stdout.write("  🔄 Limited score diversity - consider adjusting EXIF weights")
        else:
            self.stdout.write("  ✅ Good score diversity - EXIF system is working well")
        
        self.stdout.write(f"\n{self.style.SUCCESS('EXIF analysis completed successfully!')}")
