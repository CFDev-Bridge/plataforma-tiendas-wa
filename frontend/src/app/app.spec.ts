import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';

import { App } from './app';
import { READINESS_URL } from './core/health/health.service';

describe('App', () => {
  let http: HttpTestingController;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [App],
      providers: [provideRouter([]), provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  function renderBadge(): HTMLElement {
    const fixture = TestBed.createComponent(App);
    fixture.detectChanges();
    return fixture.nativeElement as HTMLElement;
  }

  it('muestra el título del panel', () => {
    const element = renderBadge();
    http.expectOne(READINESS_URL).flush({ status: 'ok', checks: { database: 'ok' } });

    expect(element.querySelector('h1')?.textContent).toContain('Panel de tiendas');
  });

  it('muestra "Verificando…" mientras espera la respuesta', () => {
    const element = renderBadge();

    expect(element.querySelector('.badge')?.textContent?.trim()).toBe('Verificando…');
    http.expectOne(READINESS_URL).flush({ status: 'ok', checks: { database: 'ok' } });
  });

  it('muestra "Operativo" cuando la API está lista', async () => {
    const fixture = TestBed.createComponent(App);
    fixture.detectChanges();

    http.expectOne(READINESS_URL).flush({ status: 'ok', checks: { database: 'ok' } });
    await fixture.whenStable();

    const badge = (fixture.nativeElement as HTMLElement).querySelector('.badge');
    expect(badge?.textContent?.trim()).toBe('Operativo');
    expect(badge?.classList).toContain('badge--ok');
  });

  it('muestra "No disponible" cuando la API responde 503', async () => {
    const fixture = TestBed.createComponent(App);
    fixture.detectChanges();

    http
      .expectOne(READINESS_URL)
      .flush(
        { status: 'unavailable', checks: { database: 'unavailable' } },
        { status: 503, statusText: 'Service Unavailable' },
      );
    await fixture.whenStable();

    const badge = (fixture.nativeElement as HTMLElement).querySelector('.badge');
    expect(badge?.textContent?.trim()).toBe('No disponible');
    expect(badge?.classList).toContain('badge--unavailable');
  });
});
