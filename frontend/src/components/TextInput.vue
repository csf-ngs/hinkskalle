<template>
  <div>
    <v-text-field v-if="type=='text'"
      :outlined="!(localState.static || readonly || disabled)" 
      hide-details="auto"
      v-model="localState.value"
      :label="label"
      :loading="localState.status=='saving'"
      :success="localState.status=='success'"
      :error="localState.status=='failed'"
      :disabled="disabled"
      :readonly="localState.static || readonly" 
      :append-icon="readonly || localState.static ? 'mdi-pencil-off-outline' : ''"
      :rules="rules"
      :required="required"
      @change="saveValue()"
    >
      <template v-slot:append-outer>
        <slot name="append"></slot>
      </template>
    </v-text-field>
    <v-textarea v-if="type=='textarea'"
      :outlined="!(localState.static || readonly || disabled)" 
      hide-details="auto"
      v-model="localState.value"
      :label="label"
      :loading="localState.status=='saving'"
      :success="localState.status=='success'"
      :error="localState.status=='failed'"
      :disabled="disabled"
      :readonly="localState.static || readonly" 
      :rules="rules"
      :required="required"
      :append-icon="readonly || localState.static ? 'mdi-pencil-off-outline' : ''"
      @change="saveValue()"
    ></v-textarea>
    <v-select v-if="type=='yesno'"
      :outlined="!(localState.static || readonly || disabled)" 
      hide-details="auto"
      v-model="localState.value"
      :label="label"
      :loading="localState.status=='saving'"
      :success="localState.status=='success'"
      :error="localState.status=='failed'"
      :disabled="disabled"
      :readonly="localState.static || readonly" 
      :rules="rules"
      :required="required"
      :append-icon="readonly || localState.static ? 'mdi-pencil-off-outline' : ''"
      :items="[ { value: false, text: 'No' }, { value: true, text: 'Yes' } ]"
      @change="saveValue()"
    ></v-select>
  </div>
  
</template>
<script lang="ts">
import Vue from 'vue';

// :append-icon="localState.static ? 'mdi-lock-outline' : null"

import { clone as _clone } from 'lodash';

interface State {
  status: string;
  value: string;
  static: boolean;
}

export default Vue.extend({
  name: 'HinkTextInput',
  props: {
    type: {
      type: String,
      default: "text",
    }, 
    label: {
      type: String,
      required: true,
    },
    field: String,
    obj: Object,
    action: String,
    readonly: {
      type: Boolean,
      default: false,
    },
    disabled: {
      type: Boolean,
      default: false,
    },
    required: {
      type: Boolean,
      default: false,
    },
    staticValue: {
      type: [ String, Boolean, Number ],
      default: undefined,
    },
    check: {
      type: Array,
      default: () => undefined,
    },
  },
  data: function(): { localState: State } {
    return {
      localState: {
        status: '',
        value: this.obj && this.field ? this.obj[this.field] : this.staticValue,
        static: this.staticValue !== undefined
      }
    };
  },
  computed: {
    rules(): Array<(val: string) => boolean | string> {
      let rules: Array<(val: string) => boolean | string> = [];
      if (this.required) {
        rules = rules.concat(
          val => !!val || 'Required!'
        )
      }
      if (this.check) {
        rules = rules.concat(this.check as any);
      }
      return rules;
    }
  },
  watch: {
    field(newVal, oldVal) {
      if (this.obj && this.field) {
        this.localState.value=this.obj[this.field];
      }
    },
    obj(newVal, oldVal) {
      if (this.obj && this.field) {
        this.localState.value=this.obj[this.field];
      }
    },
    staticValue(newVal, oldVal) {
      this.localState.value=newVal;
      this.localState.static = newVal !== undefined;
    },
  },
  methods: {
    saveValue() {
      const obj = _clone(this.obj);
      obj[this.field] = this.localState.value;
      if (!this.action) {
        return this.$emit('updated', obj);
      }
      this.localState.status='saving';
      this.$store.dispatch(this.action, obj)
        .then(updated => {
          this.localState.status='success';
          this.$emit('updated', updated);
        })
        .catch(err => {
          this.localState.status='failed';
          this.$store.commit('snackbar/showError', err);
        });
    }
  },
})
</script>