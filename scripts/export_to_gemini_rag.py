#!/usr/bin/env python3
"""
Export industry articles to Gemini RAG corpus
Uploads high-value articles to Gemini File API for knowledge base
"""

import os
import sys
import json
import tempfile
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

try:
    import google.generativeai as genai
except ImportError:
    print("❌ google-generativeai not installed. Run: pip install google-generativeai")
    sys.exit(1)

try:
    from sqlalchemy.orm import Session
except ImportError:
    print("❌ sqlalchemy not installed. Run: pip install sqlalchemy psycopg2-binary")
    sys.exit(1)

# Add database utilities to path
sys.path.insert(0, str(Path(__file__).parent / "database"))
from db_utils import IndustryKnowledgeDB
from models import IndustryArticle


class GeminiRAGExporter:
    """Export industry articles to Gemini RAG corpus"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY required. Get from https://aistudio.google.com")

        genai.configure(api_key=self.api_key)
        self.db = IndustryKnowledgeDB()

    def prepare_article_for_rag(self, article: IndustryArticle) -> Dict:
        """Convert article to RAG-friendly format"""

        # Get topic names
        topics = [t.name for t in article.topics] if article.topics else []

        # Build structured document
        doc = {
            'title': article.title,
            'source': article.site.name,
            'category': article.site.category.value,
            'url': article.url,
            'published': article.published_at.isoformat() if article.published_at else None,
            'topics': topics,
            'relevance_score': article.relevance_score,
            'word_count': article.word_count,
            'content': article.content_markdown
        }

        return doc

    def create_document_text(self, article: IndustryArticle) -> str:
        """Create formatted text for Gemini upload"""

        topics = [t.name for t in article.topics] if article.topics else []

        # Format as structured markdown
        doc_text = f"""# {article.title}

**Source**: {article.site.name}
**Category**: {article.site.category.value}
**Published**: {article.published_at.strftime('%Y-%m-%d') if article.published_at else 'Unknown'}
**URL**: {article.url}
**Topics**: {', '.join(topics)}
**Relevance Score**: {article.relevance_score}/60
**Words**: {article.word_count:,}

---

{article.content_markdown}

---

**Metadata for RAG**:
- Primary Topics: {', '.join(topics[:5])}
- Industry: Sign Manufacturing, Metal Fabrication, Engineering
- Content Type: {article.site.category.value}
- Relevance: {article.relevance_level.value}
"""
        return doc_text

    def upload_to_gemini(self, article: IndustryArticle) -> Optional[str]:
        """Upload single article to Gemini File API"""

        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
                doc_text = self.create_document_text(article)
                f.write(doc_text)
                temp_path = f.name

            # Upload file
            print(f"  📤 Uploading: {article.title[:60]}...")

            file = genai.upload_file(
                path=temp_path,
                display_name=f"{article.site.name} - {article.title[:100]}"
            )

            # Clean up temp file
            os.unlink(temp_path)

            print(f"     ✅ Uploaded: {file.name}")
            return file.name

        except Exception as e:
            print(f"     ❌ Failed: {e}")
            return None

    def export_batch(
        self,
        session: Session,
        limit: int = 100,
        min_relevance_score: int = 5
    ) -> Dict:
        """Export batch of articles to Gemini"""

        print(f"\n{'='*80}")
        print("📤 EXPORTING ARTICLES TO GEMINI RAG")
        print(f"{'='*80}\n")

        # Get articles not yet in RAG
        articles = self.db.get_articles_for_rag(session, limit=limit)

        # Filter by minimum relevance
        articles = [a for a in articles if a.relevance_score >= min_relevance_score]

        if not articles:
            print("✅ No new articles to export (all caught up!)")
            return {
                'total': 0,
                'uploaded': 0,
                'failed': 0,
                'skipped': 0
            }

        print(f"Found {len(articles)} high-value articles to upload\n")

        stats = {
            'total': len(articles),
            'uploaded': 0,
            'failed': 0,
            'skipped': 0
        }

        # Upload each article
        for idx, article in enumerate(articles, 1):
            print(f"[{idx}/{len(articles)}] {article.site.name}")

            # Upload to Gemini
            file_id = self.upload_to_gemini(article)

            if file_id:
                # Mark as added in database
                self.db.mark_added_to_rag(session, article.id, file_id)
                stats['uploaded'] += 1
            else:
                stats['failed'] += 1

            # Rate limiting: pause every 10 uploads
            if idx % 10 == 0 and idx < len(articles):
                print("\n  ⏸️  Pausing 2 seconds (rate limiting)...\n")
                import time
                time.sleep(2)

        # Summary
        print(f"\n{'='*80}")
        print("📊 EXPORT SUMMARY")
        print(f"{'='*80}\n")
        print(f"Total Articles: {stats['total']}")
        print(f"✅ Uploaded: {stats['uploaded']}")
        print(f"❌ Failed: {stats['failed']}")
        print(f"⏭️  Skipped: {stats['skipped']}")

        success_rate = (stats['uploaded'] / stats['total'] * 100) if stats['total'] > 0 else 0
        print(f"\nSuccess Rate: {success_rate:.1f}%")

        return stats

    def list_uploaded_files(self) -> List:
        """List all files in Gemini"""
        try:
            files = genai.list_files()
            return list(files)
        except Exception as e:
            print(f"❌ Error listing files: {e}")
            return []

    def create_corpus(self, corpus_name: str = "industry_knowledge") -> str:
        """Create a Gemini corpus for organizing articles"""
        try:
            # Note: Corpus creation requires Gemini API Pro
            print(f"📦 Creating corpus: {corpus_name}")

            # For now, just use file uploads
            # Full corpus support requires:
            # corpus = genai.create_corpus(display_name=corpus_name)

            print("  ℹ️  Using file-based uploads (corpus requires Gemini Pro)")
            return "file-based"

        except Exception as e:
            print(f"  ⚠️  Corpus creation not available: {e}")
            return "file-based"

    def export_report(self, stats: Dict, output_file: Optional[str] = None):
        """Generate export report"""

        if not output_file:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f"./gemini_export_report_{timestamp}.json"

        report = {
            'timestamp': datetime.now().isoformat(),
            'statistics': stats,
            'gemini_api_key': self.api_key[:10] + "..." + self.api_key[-5:],  # Partial for verification
            'database_url': os.getenv('DATABASE_URL', 'not set')
        }

        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"\n💾 Report saved: {output_file}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Export industry articles to Gemini RAG")
    parser.add_argument('--limit', type=int, default=100,
                        help='Maximum articles to export (default: 100)')
    parser.add_argument('--min-score', type=int, default=5,
                        help='Minimum relevance score (default: 5)')
    parser.add_argument('--list', action='store_true',
                        help='List already uploaded files')
    parser.add_argument('--api-key', type=str,
                        help='Gemini API key (or set GEMINI_API_KEY env var)')
    args = parser.parse_args()

    # Check API key
    api_key = args.api_key or os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ No Gemini API key found!\n")
        print("Get free key from: https://aistudio.google.com\n")
        print("Then set environment variable:")
        print("  export GEMINI_API_KEY='your-key'  # Linux/Mac")
        print("  $env:GEMINI_API_KEY='your-key'    # PowerShell\n")
        print("Or pass as argument:")
        print("  python export_to_gemini_rag.py --api-key your-key")
        sys.exit(1)

    try:
        exporter = GeminiRAGExporter(api_key)

        # List mode
        if args.list:
            print("\n📋 Files in Gemini:\n")
            files = exporter.list_uploaded_files()
            for idx, file in enumerate(files, 1):
                print(f"{idx}. {file.display_name}")
                print(f"   ID: {file.name}")
                print(f"   Size: {file.size_bytes:,} bytes\n")
            print(f"Total: {len(files)} files")
            return

        # Export mode
        session = exporter.db.get_session()
        try:
            stats = exporter.export_batch(
                session,
                limit=args.limit,
                min_relevance_score=args.min_score
            )

            # Generate report
            exporter.export_report(stats)

            print("\n✅ Export complete!")

            if stats['uploaded'] > 0:
                print("\n💡 Next steps:")
                print("  1. Use Gemini File API to query uploaded documents")
                print("  2. Create grounding queries in Gemini Studio")
                print("  3. Integrate with SignX quote generation")

        finally:
            session.close()

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
