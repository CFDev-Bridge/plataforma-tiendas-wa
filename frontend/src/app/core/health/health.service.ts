import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable, catchError, map, of } from 'rxjs';

export type ServiceStatus = 'checking' | 'ok' | 'unavailable';

interface ReadinessResponse {
  readonly status: 'ok' | 'unavailable';
  readonly checks: Readonly<Record<string, 'ok' | 'unavailable'>>;
}

export const READINESS_URL = '/health/ready';

@Injectable({ providedIn: 'root' })
export class HealthService {
  private readonly http = inject(HttpClient);

  /** Consulta la disponibilidad de la API y sus dependencias. Nunca emite error. */
  checkReadiness(): Observable<ServiceStatus> {
    return this.http.get<ReadinessResponse>(READINESS_URL).pipe(
      map((response) => (response.status === 'ok' ? 'ok' : 'unavailable')),
      catchError(() => of<ServiceStatus>('unavailable')),
    );
  }
}
