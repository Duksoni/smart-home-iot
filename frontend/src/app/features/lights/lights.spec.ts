import {ComponentFixture, TestBed} from '@angular/core/testing';

import {Lights} from './lights';

describe('Lights', () => {
    let component: Lights;
    let fixture: ComponentFixture<Lights>;

    beforeEach(async () => {
        await TestBed.configureTestingModule({
            imports: [Lights]
        })
            .compileComponents();

        fixture = TestBed.createComponent(Lights);
        component = fixture.componentInstance;
        await fixture.whenStable();
    });

    it('should create', () => {
        expect(component).toBeTruthy();
    });
});
