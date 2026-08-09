import { ComponentFixture, TestBed } from '@angular/core/testing';

import { Brevet } from './brevet';

describe('Brevet', () => {
  let component: Brevet;
  let fixture: ComponentFixture<Brevet>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Brevet],
    }).compileComponents();

    fixture = TestBed.createComponent(Brevet);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
