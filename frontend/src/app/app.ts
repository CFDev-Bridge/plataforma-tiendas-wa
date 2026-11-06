import { ChangeDetectionStrategy, Component, computed, inject } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { RouterOutlet } from '@angular/router';

import { HealthService, ServiceStatus } from './core/health/health.service';

const STATUS_LABELS: Readonly<Record<ServiceStatus, string>> = {
  checking: 'Verificando…',
  ok: 'Operativo',
  unavailable: 'No disponible',
};

@Component({
  imports: [RouterOutlet],
  selector: 'app-root',
  styleUrl: './app.scss',
  templateUrl: './app.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class App {
  private readonly health = inject(HealthService);

  protected readonly apiStatus = toSignal(this.health.checkReadiness(), {
    initialValue: 'checking' satisfies ServiceStatus as ServiceStatus,
  });
  protected readonly statusLabel = computed(() => STATUS_LABELS[this.apiStatus()]);
}
