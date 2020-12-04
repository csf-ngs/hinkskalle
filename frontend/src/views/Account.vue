<template>
  <div class="account">
    <top-bar title="Account"></top-bar>
    <v-container>
      <v-row v-if="localState.editUser">
        <v-col cols="12" md="8" offset-md="2">
          <v-form v-model="localState.editValid">
            <v-container>
              <v-row>
                <v-col cols="12" md="6">
                  <hsk-text-input id="firstname" 
                    label="Firstname"
                    field="firstname"
                    :obj="localState.editUser"
                    :readonly="localState.editUser.source!='local'"
                    required
                    @updated="localState.editUser=$event"></hsk-text-input>
                </v-col>
                <v-col cols="12" md="6">
                  <hsk-text-input id="lastname" 
                    label="Lastname"
                    field="lastname"
                    :obj="localState.editUser"
                    :readonly="localState.editUser.source!='local'"
                    required
                    @updated="localState.editUser=$event"></hsk-text-input>
                </v-col>
                <v-col cols="12" md="6">
                  <hsk-text-input id="username" 
                    :static-value="localState.editUser.username"
                    label="Username"></hsk-text-input>
                </v-col>
                <v-col cols="12" md="6">
                  <hsk-text-input id="email" 
                    label="Email"
                    field="email"
                    :obj="localState.editUser"
                    :readonly="localState.editUser.source!='local'"
                    required
                    @updated="localState.editUser=$event"></hsk-text-input>
                </v-col>
              </v-row>
              <v-row>
                <v-col cols="12">
                  <v-spacer></v-spacer>
                  <v-btn type="reset" color="secondary accent-1" text @click.prevent="reset()">Reset</v-btn>
                  <v-btn type="submit" color="primary darken-1" text :disabled="!localState.editValid" @click.prevent="update()">Save</v-btn>
                </v-col>
              </v-row>
            </v-container>
          </v-form>
        </v-col>
      </v-row>
    </v-container>
  </div>
</template>
<script lang="ts">
import Vue from 'vue';
import { User } from '../store/models';

import { clone as _clone } from 'lodash';

interface State {
  editUser: User | null;
  editValid: boolean;
}

export default Vue.extend({
  name: 'Account',
  data: (): { localState: State } => ({
    localState: {
      editUser: null,
      editValid: true,
    },
  }),
  mounted: function() {
    this.localState.editUser = _clone(this.$store.getters.currentUser);
  },
  methods: {
    reset() {
      this.localState.editUser = _clone(this.$store.getters.currentUser);
    },
    update() {
      this.$store.dispatch('users/update', this.localState.editUser)
        .then(user => {
          this.$store.commit('setUser', user);
          this.localState.editUser = _clone(this.$store.getters.currentUser);
          this.$store.commit('snackbar/showSuccess', "Hooray!");
        })
        .catch(err => this.$store.commit('snackbar/showError', err));
    },
  }
});
</script>