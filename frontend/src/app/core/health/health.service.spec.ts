import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { firstValueFrom } from 'rxjs';

import { HealthService, READINESS_URL } from './health.service';

describe('HealthService', () => {
  let service: HealthService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(HealthService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('informa ok cuando la API está lista', async () => {
    const result = firstValueFrom(service.checkReadiness());

    http.expectOne(READINESS_URL).flush({ status: 'ok', checks: { database: 'ok' } });

    expect(await result).toBe('ok');
  });

  it('informa unavailable cuando la API responde 503', async () => {
    const result = firstValueFrom(service.checkReadiness());

    http
      .expectOne(READINESS_URL)
      .flush(
        { status: 'unavailable', checks: { database: 'unavailable' } },
        { status: 503, statusText: 'Service Unavailable' },
      );

    expect(await result).toBe('unavailable');
  });

  it('informa unavailable cuando falla la red', async () => {
    const result = firstValueFrom(service.checkReadiness());

    http.expectOne(READINESS_URL).error(new ProgressEvent('error'));

    expect(await result).toBe('unavailable');
  });
});
