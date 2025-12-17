import { useState, useCallback, useEffect } from 'react';
import { Header } from '@/components/layout/Header';
import { DashboardSidebar } from '@/components/dashboard/DashboardSidebar';
import { ProjectUpload } from '@/components/dashboard/ProjectUpload';
import { ReviewProgressDisplay } from '@/components/dashboard/ReviewProgress';
import { ReviewResults } from '@/components/dashboard/ReviewResults';
import { EmptyState } from '@/components/dashboard/EmptyState';
import { useAuth } from '@/contexts/AuthContext';
import { mockApi } from '@/services/mockApi';
import { useToast } from '@/hooks/use-toast';
import type { ReviewResult, ReviewStep } from '@/types';

type DashboardState = 'idle' | 'uploading' | 'processing' | 'complete';

const REVIEWS_STORAGE_KEY = 'smartcodex_reviews';

export default function Dashboard() {
  const { user } = useAuth();
  const { toast } = useToast();

  const [state, setState] = useState<DashboardState>('idle');
  const [currentStep, setCurrentStep] = useState<ReviewStep>('extracting');
  const [progress, setProgress] = useState(0);
  const [selectedReview, setSelectedReview] = useState<ReviewResult | null>(null);
  const [reviews, setReviews] = useState<ReviewResult[]>([]);
  const [showUpload, setShowUpload] = useState(true);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  // Fetch reviews from backend on mount
  useEffect(() => {
    const fetchReviews = async () => {
      try {
        const token = localStorage.getItem('smartcodex_token');
        const response = await fetch('http://localhost:8000/reviews', {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        if (response.ok) {
          const data = await response.json();
          setReviews(data);
        }
      } catch (error) {
        console.error('Failed to fetch reviews:', error);
      }
    };

    if (user) {
      fetchReviews();
    }
  }, [user]);

  const simulateProcessing = useCallback(async () => {
    const steps: ReviewStep[] = ['extracting', 'analyzing', 'reviewing', 'generating'];

    for (let i = 0; i < steps.length; i++) {
      setCurrentStep(steps[i]);
      const startProgress = (i / steps.length) * 100;
      const endProgress = ((i + 1) / steps.length) * 100;

      for (let p = startProgress; p <= endProgress; p += 2) {
        setProgress(p);
        await new Promise(resolve => setTimeout(resolve, 50));
      }
    }
  }, []);

  const saveReviewToBackend = async (review: ReviewResult) => {
    try {
      const token = localStorage.getItem('smartcodex_token');
      await fetch('http://localhost:8000/reviews', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(review)
      });
      // Re-fetch or manually update state (state update is already done in handlers)
    } catch (error) {
      console.error('Failed to save review:', error);
      toast({
        title: "Warning",
        description: "Review generated but failed to save to history.",
        variant: "destructive"
      });
    }
  };

  const handleFileUpload = useCallback(async (file: File) => {
    setState('uploading');
    setProgress(0);

    try {
      toast({
        title: 'Uploading project...',
        description: file.name,
      });

      const uploadProgress = (p: number) => {
        setProgress(p * 0.25);
      };

      setState('processing');
      await simulateProcessing();

      const reviewResult = await mockApi.review.upload(file, uploadProgress);

      await saveReviewToBackend(reviewResult);

      setReviews(prev => [reviewResult, ...prev]);
      setSelectedReview(reviewResult);
      setState('complete');
      setShowUpload(false);

      toast({
        title: 'Analysis complete!',
        description: `Found ${reviewResult.totalIssues} issues across ${reviewResult.totalFiles} files.`,
      });
    } catch (error) {
      setState('idle');
      toast({
        title: 'Upload failed',
        description: error instanceof Error ? error.message : 'Something went wrong',
        variant: 'destructive',
      });
    }
  }, [simulateProcessing, toast]);

  const handleGithubSubmit = useCallback(async (url: string) => {
    setState('processing');
    setProgress(0);

    try {
      toast({
        title: 'Fetching repository...',
        description: url,
      });

      await simulateProcessing();

      const reviewResult = await mockApi.review.github(url);

      await saveReviewToBackend(reviewResult);

      setReviews(prev => [reviewResult, ...prev]);
      setSelectedReview(reviewResult);
      setState('complete');
      setShowUpload(false);

      toast({
        title: 'Analysis complete!',
        description: `Found ${reviewResult.totalIssues} issues across ${reviewResult.totalFiles} files.`,
      });
    } catch (error) {
      setState('idle');
      toast({
        title: 'Analysis failed',
        description: error instanceof Error ? error.message : 'Something went wrong',
        variant: 'destructive',
      });
    }
  }, [simulateProcessing, toast]);

  const handleNewReview = useCallback(() => {
    setState('idle');
    setSelectedReview(null);
    setShowUpload(true);
    setProgress(0);
  }, []);

  const handleSelectReview = useCallback((review: ReviewResult) => {
    setSelectedReview(review);
    setState('complete');
    setShowUpload(false);
  }, []);

  const handleDeleteReview = useCallback(async (id: string) => {
    // Optimistic Update: Remove immediately
    const previousReviews = reviews;
    setReviews(prev => prev.filter(r => r.id !== id));

    // If the deleted review was selected, deselect it immediately
    if (selectedReview?.id === id) {
      setSelectedReview(null);
      setShowUpload(true);
      setState('idle');
    }

    try {
      const token = localStorage.getItem('smartcodex_token');
      const response = await fetch(`http://localhost:8000/reviews/${id}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to delete review');
      }

      toast({
        title: "Review deleted",
        description: "The review has been permanently deleted."
      });
    } catch (error) {
      // Revert on failure
      setReviews(previousReviews);

      toast({
        title: "Error",
        description: "Failed to delete review",
        variant: "destructive"
      });
    }
  }, [reviews, selectedReview, toast]);

  const isProcessing = state === 'uploading' || state === 'processing';

  return (
    <div className="min-h-screen bg-background flex flex-col">
      <Header />

      <div className="flex flex-1 overflow-hidden">
        <DashboardSidebar
          reviews={reviews}
          selectedReviewId={selectedReview?.id || null}
          onSelectReview={handleSelectReview}
          onNewReview={handleNewReview}
          onDeleteReview={handleDeleteReview}
          isCollapsed={sidebarCollapsed}
          onToggleCollapse={() => setSidebarCollapsed(!sidebarCollapsed)}
        />

        <main className="flex-1 overflow-auto">
          <div className="container py-8">
            <div className="mb-8 flex items-end gap-2">
              <div>
                <h1 className="text-3xl font-bold flex items-center gap-2">
                  Welcome back, <span className="text-gradient">{user?.username}</span>
                </h1>
                <p className="text-muted-foreground mt-1">
                  Upload your project to get started with AI-powered code review.
                </p>
              </div>
            </div>

            {showUpload && state === 'idle' && !selectedReview && (
              <div className="max-w-2xl mx-auto">
                <ProjectUpload
                  onUpload={handleFileUpload}
                  onGithubSubmit={handleGithubSubmit}
                  isLoading={isProcessing}
                />
              </div>
            )}

            {isProcessing && (
              <div className="max-w-2xl mx-auto">
                <ReviewProgressDisplay currentStep={currentStep} progress={progress} />
              </div>
            )}

            {state === 'complete' && selectedReview && (
              <ReviewResults result={selectedReview} onNewReview={handleNewReview} />
            )}

            {state === 'idle' && !showUpload && !selectedReview && reviews.length === 0 && (
              <EmptyState onUploadClick={() => setShowUpload(true)} />
            )}
          </div>
        </main>
      </div>
    </div>
  );
}
