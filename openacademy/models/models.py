# -*- coding: utf-8 -*-

from datetime import timedelta
from odoo import models, fields, api, exceptions, _
from ..reports.custom_report import CustomReport



class Course(models.Model):
    _name = 'openacademy.course'
    _description = "OpenAcademy Courses"

    name = fields.Char(string=_("Title"), required=True)
    description = fields.Text(required=True)

    responsible_id = fields.Many2one('res.users',
                                     ondelete='set null',
                                     string=_("Responsible"),
                                     index=True)
    session_ids = fields.One2many(
        'openacademy.session', 'course_id', string="Sessions")

    @api.model
    def create(self, vals):
        rec = super(Course, self).create(vals)
        print("Creating some record/s...", flush=True)
        print(rec, flush=True)
        return rec

    def copy(self, default=None):
        default = dict(default or {})

        copied_count = self.search_count(
            [('name', '=like', _(u"Copy of {}%").format(self.name))])
        if not copied_count:
            new_name = _(u"Copy of {}").format(self.name)
        else:
            new_name = _(u"Copy of {} ({})").format(self.name, copied_count)

        default['name'] = new_name
        return super(Course, self).copy(default)

    @api.constrains('name', 'description')
    def _check_name_and_description(self):
        for r in self:
            if r.name and r.description:
                unique = self.env['openacademy.course'].search(
                    ['&',
                        ["name", "ilike", self.name],
                        ["id", "!=", self.id]]
                )
                if unique:
                    raise exceptions.ValidationError(
                        "The course title must be unique"
                    )
                if r.name.lower() == r.description.lower():
                    raise exceptions.ValidationError(
                        "The title of the course should not be the description"
                    )


class Session(models.Model):
    _name = 'openacademy.session'
    _description = "OpenAcademy Sessions"

    @api.depends('start_date', 'duration')
    def _get_end_date(self):
        for r in self:
            if not (r.start_date and r.duration):
                r.end_date = r.start_date
                continue

            duration = timedelta(days=r.duration, seconds=-1)
            r.end_date = r.start_date + duration

    def _set_end_date(self):
        for r in self:
            if not (r.start_date and r.end_date):
                continue

            r.duration = (r.end_date - r.start_date).days + 1

    @api.depends('attendee_ids')
    def _get_attendees_count(self):
        for r in self:
            r.attendees_count = len(r.attendee_ids)

    name = fields.Char(required=True)
    start_date = fields.Date(default=fields.Date.today)
    end_date = fields.Date()
    duration = fields.Float(digits=(6, 2), help="Duration in days")
    seats = fields.Integer(string="Number of seats")
    active = fields.Boolean(default=True)
    color = fields.Integer()

    instructor_id = fields.Many2one('res.partner',
                                     string="Instructor",
                                    domain=['|',
                                            ('instructor', '=', True),
                                            ('category_id.name',
                                             'ilike',
                                             "Teacher")])

    course_id = fields.Many2one('openacademy.course',
                            ondelete='cascade',
                                string="Course",
                                required=True)
    attendee_ids = fields.Many2many('res.partner', string="Attendees")
    taken_seats = fields.Float(string="Taken seats", compute='_taken_seats')
    end_date = fields.Date(string="End Date",
                           store=True,
                           compute='_get_end_date',
                           inverse='_set_end_date')

    is_done = fields.Boolean(string="Session Done?", default=False, readonly=True)

    attendees_count = fields.Integer(string="Attendees count",
                                     compute='_get_attendees_count',
                                     store=True)

    report_attachment_ids = fields.One2many(
        'ir.attachment', 'res_id',
        domain=[
            ('res_model', '=', 'openacademy.session')
        ],
        string='Custom Reports'
    )

    @api.depends('seats', 'attendee_ids')
    def _taken_seats(self):
        for r in self:
            if not r.seats:
                r.taken_seats = 0.0
            else:
                r.taken_seats = 100.0 * len(r.attendee_ids) / r.seats

    @api.onchange('seats', 'attendee_ids')
    def _verify_valid_seats(self):
        if self.seats < 0:
            return {
                'warning': {
                    'title': _("Incorrect 'seats' value"),
                    'message': _(
                        "The number of available seats may not be negative"
                    ),
                },
            }
        elif self.seats < len(self.attendee_ids):
            return {
                'warning': {
                    'title': _("Too many attendees"),
                    'message': _("Increase seats or remove excess attendees"),
                },
            }

    @api.constrains('instructor_id', 'attendees_count')
    def _check_max_student(self):
        for r in self:
            if r.attendees_count > r.instructor_id.max_student:
                raise exceptions.ValidationError(
                    _(
                        "The Instructor can only handle %s Student"
                    ) % r.instructor_id.max_student
                )

    @api.onchange('seats', 'instructor_id')
    def _change_seats_count(self):
        if self.seats > self.instructor_id.max_student:
            return {
                'warning': {
                    'title': _("Too many seats"),
                    'message': _(
                        "Instructor of this session takes only %s students"
                    ) % self.instructor_id.max_student,
                },
            }

    @api.constrains('instructor_id', 'attendee_ids')
    def _check_instructor_not_in_attendees(self):
        for r in self:
            if r.instructor_id and r.instructor_id in r.attendee_ids:
                raise exceptions.ValidationError(
                    _(
                        "A session's instructor can't be an attendee"
                    )
                )

    def mark_as_done(self):
        self.is_done = True
        return {}

    def _get_printout_data(self):
        company = self.instructor_id.company_id
        instructor = self.instructor_id
        data = {
            'name': self.name,
            'instructor': {
                'instructor_name': instructor.name,
                'instructor_tin':  instructor.vat,

            },
            'company': {
                'company_name': company.name,
                'company_address': "%s, %s, %s" % (
                    company.street, company.city, company.state_id.name
                )
            },
            'start_date': self.start_date,
            'end_date': self.end_date,
        }

        report = CustomReport(**data)
        return report

    def action_print_report(self):
        report_file = self._get_printout_data()
        report_file = report_file.print()

        file_name = f'session_custom_report_{self.name}'
        args = [
            ("name", "ilike", file_name)
        ]
        existing_reports = self.env['ir.attachment'].search_count(args)
        if existing_reports:
            file_name = "%s(%s)" % (
                file_name, existing_reports
            )

        attachment_id = self.env['ir.attachment'].create({
            'name': f"{file_name}.pdf",
            'type': 'binary',
            'datas': report_file,
            'res_model': self._name,
            'res_id': self.id,
            'mimetype': 'application/x-pdf'
        })
        ctx = {
            'default_model': self._name,
            'default_res_id': self.id,
            'default_composition_mode': 'comment',
        }

        compose = self.env['mail.mail'].with_context(ctx).create({
            'subject': '%s' % 'Generated Report',
            'body_html': 'Report Generated',
            'attachment_ids': [(6, 0, [attachment_id.id])] or None,
        })
        return
