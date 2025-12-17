import { useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { Loader2 } from 'lucide-react';

export default function AuthCallback() {
    const [searchParams] = useSearchParams();
    const navigate = useNavigate();
    const { loginWithToken } = useAuth();

    useEffect(() => {
        const token = searchParams.get('token');
        if (token) {
            loginWithToken(token).then(() => {
                navigate('/dashboard', { replace: true });
            }).catch((err) => {
                console.error("Login failed", err);
                navigate('/auth?error=login_failed', { replace: true });
            });
        } else {
            navigate('/auth', { replace: true });
        }
    }, [searchParams, loginWithToken, navigate]);

    return (
        <div className="min-h-screen flex items-center justify-center bg-background">
            <div className="flex flex-col items-center gap-4">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
                <p className="text-muted-foreground">Signing you in...</p>
            </div>
        </div>
    );
}
