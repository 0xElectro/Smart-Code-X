import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { FileSearch, Upload, ArrowRight } from 'lucide-react';

interface EmptyStateProps {
  onUploadClick: () => void;
}

export function EmptyState({ onUploadClick }: EmptyStateProps) {
  return (
    <Card className="bg-card/50 backdrop-blur-sm border-border/50">
      <CardContent className="flex flex-col items-center justify-center py-16">
        <div className="h-20 w-20 rounded-full bg-primary/10 flex items-center justify-center mb-6">
          <FileSearch className="h-10 w-10 text-primary" />
        </div>
        <h3 className="text-xl font-semibold mb-2">No Reviews Yet</h3>
        <p className="text-muted-foreground text-center max-w-md mb-6">
          Upload your first project to get started with AI-powered code review.
          We'll analyze your code for issues, vulnerabilities, and improvements.
        </p>
        <Button onClick={onUploadClick} className="bg-gradient-primary hover:opacity-90">
          <Upload className="mr-2 h-4 w-4" />
          Upload Project
          <ArrowRight className="ml-2 h-4 w-4" />
        </Button>
      </CardContent>
    </Card>
  );
}
