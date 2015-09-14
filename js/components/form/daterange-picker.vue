<style lang="less">
.daterange-picker {
    .dropdown-menu {
        min-width:auto;
        width:100%;
    }
}
</style>

<template>
<div class="input-group dropdown daterange-picker" v-class="open: picking">
    <span class="input-group-addon"><span class="fa fa-calendar"></span></span>
    <input type="text" class="input-sm form-control"
        v-el="startInput" placeholder="{{ _('Start') }}"
        v-on="focus: onFocus, blur: onBlur"
        v-attr="
            required: required,
            value: start_value,
            readonly: readonly || false
        ">
    <span class="input-group-addon">à</span>
    <input type="text" class="input-sm form-control"
        v-el="endInput" placeholder="{{ _('End') }}"
        v-on="focus: onFocus, blur: onBlur"
        v-attr="
            required: required,
            value: end_value,
            readonly: readonly || false
        ">
    <div class="dropdown-menu dropdown-menu-right">
        <calendar selected="{{value}}"></calendar>
    </div>
    <input type="hidden" v-el="startHidden"
        v-attr="
            id: field.id + '-start',
            name: field.id + '.start',
            value: start_value
        "></input>
    <input type="hidden" v-el="endHidden"
        v-attr="
            id: field.id + '-end',
            name: field.id + '.end',
            value: end_value
        "></input>
</div>
</template>

<script>
const DEFAULT_FORMAT = 'L',
      ISO_FORMAT = 'YYYY-MM-DD';


export default {
    name: 'daterange-picker',
    replace: true,
    mixins: [require('components/form/base-field').FieldComponentMixin],
    components: {
        calendar: require('components/calendar.vue')
    },
    data: function() {
        return {
            picking: false,
            pickedField: null,
            hiddenField: null
        };
    },
    computed: {
        start_value: function() {
            return this.value && this.value.hasOwnProperty('start')
                ? this.value.start
                : '';
        },
        end_value: function() {
            return this.value && this.value.hasOwnProperty('end')
                ? this.value.end
                : '';
        }
    },
    events: {
        'calendar:date:selected': function(date) {
            this.pickedField.value = date.format(this.field.format || DEFAULT_FORMAT);
            this.hiddenField.value = date.format(ISO_FORMAT);
            this.picking = false;
        },
        'calendar:date:cleared': function() {
            this.pickedField.value = '';
            this.hiddenField.value = '';
            this.picking = false;
        }
    },
    methods: {
        onFocus: function(e) {
            this.picking = true;
            this.pickedField = e.target;
            this.hiddenField = e.target == this.$$.startInput
                ? this.$$.startHidden
                : this.$$.endHidden;
        },
        onBlur: function(e) {
            if (e.targetVM !== this) {
                this.picking = false;
            }
        }
    },
    ready: function() {
        // Perform all validations on end field because performing on start field unhighlight.
        $(this.$$.endHidden).rules('add', {
            dateGreaterThan: '#' + this.$$.startHidden.id,
            required: (el) => {
                return (this.$$.startHidden.value && !this.$$.endHidden.value) || (this.$$.endHidden.value && !this.$$.startHidden.value);
            },
            messages: {
                dateGreaterThan: this._('End date should be after start date'),
                required: this._('Both dates are required')
            }
        });
    }
};
</script>