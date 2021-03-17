<template>
  <div class="users">
    <top-bar title="Users"></top-bar>
    <v-container>
      <v-row>
        <v-col cols="12" md="10" offset-md="1">
          <v-data-table
            id="users"
            :headers="headers"
            :items="users"
            :search="localState.search"
            :sort-by="localState.sortBy"
            :sort-desc="localState.sortDesc"
            :loading="loading">
            <template v-slot:top>
              <v-toolbar flat>
                <v-text-field 
                  v-model="localState.search" 
                  prepend-inner-icon="mdi-magnify" 
                  label="Search..." 
                  single-line outlined dense hide-details></v-text-field>
                <v-spacer></v-spacer>
                <v-dialog v-model="localState.showEdit" max-width="700px">
                  <template v-slot:activator="{ on, attrs }">
                    <v-btn
                      dense depressed
                      v-bind="attrs" v-on="on">Create User</v-btn>
                  </template>
                  <v-card>
                    <v-card-title class="headline">{{editTitle}}</v-card-title>
                    <v-card-text>
                      <v-container>
                        <v-form v-model="localState.editValid">
                        <v-row>
                          <v-col cols="12">
                            <hsk-text-input
                              id="username"
                              label="Username"
                              field="username"
                              :obj="localState.editItem"
                              :readonly="!!localState.editItem.id"
                              required
                              @updated="localState.editItem=$event"></hsk-text-input>
                          </v-col>
                          <v-col cols="12" md="6">
                            <hsk-text-input
                              id="firstname"
                              label="Firstname"
                              field="firstname"
                              :obj="localState.editItem"
                              :readonly="localState.editItem.source!='local'"
                              required
                              @updated="localState.editItem=$event"></hsk-text-input>
                          </v-col>
                          <v-col cols="12" md="6">
                            <hsk-text-input
                              id="lastname"
                              label="Lastname"
                              field="lastname"
                              :obj="localState.editItem"
                              :readonly="localState.editItem.source!='local'"
                              required
                              @updated="localState.editItem=$event"></hsk-text-input>
                          </v-col>
                          <v-col cols="12">
                            <hsk-text-input
                              id="email"
                              label="Email"
                              field="email"
                              :obj="localState.editItem"
                              :readonly="localState.editItem.source!='local'"
                              required
                              @updated="localState.editItem=$event"></hsk-text-input>
                          </v-col>
                          <v-col cols="12" md="6" v-if="localState.editItem.source=='local'">
                            <v-text-field
                              :type="localState.passwordVisible ? 'text' : 'password'"
                              outlined
                              v-model="localState.password1"
                              label="Password"
                              :hint="localState.editItem.id ? 'leave empty to keep old' : ''"
                              :error="!passwordsMatching"
                              :append-icon="localState.passwordVisible ? 'mdi-eye' : 'mdi-eye-off'"
                              @click:append="localState.passwordVisible=!localState.passwordVisible"
                              ></v-text-field>
                          </v-col>
                          <v-col cols="12" md="6" v-if="localState.editItem.source=='local'">
                            <v-text-field
                              :type="localState.passwordVisible ? 'text' : 'password'"
                              outlined
                              v-model="localState.password2"
                              label="Repeat"
                              :error="!passwordsMatching"
                              :append-icon="localState.passwordVisible ? 'mdi-eye' : 'mdi-eye-off'"
                              @click:append="localState.passwordVisible=!localState.passwordVisible"
                              ></v-text-field>
                          </v-col>
                          <v-col cols="12" md="6">
                            <hsk-text-input 
                              type="yesno"
                              label="Active?"
                              field="isActive"
                              :readonly="localState.editItem.id==currentUser.id"
                              :obj="localState.editItem"
                              @updated="localState.editItem=$event"></hsk-text-input>
                          </v-col>
                          <v-col cols="12" md="6">
                            <hsk-text-input 
                              type="yesno"
                              label="Admin?"
                              field="isAdmin"
                              :obj="localState.editItem"
                              @updated="localState.editItem=$event"></hsk-text-input>
                          </v-col>
                        </v-row>
                        </v-form>
                      </v-container>
                    </v-card-text>
                    <v-card-actions>
                      <v-spacer></v-spacer>
                      <v-btn color="secondary accent-1" text @click="closeEdit">Mabye not today.</v-btn>
                      <v-btn color="primary darken-1" :disabled="!localState.editValid" text @click="save">Save It!</v-btn>
                    </v-card-actions>
                  </v-card>
                </v-dialog>
                <v-dialog v-model="localState.showDelete" max-width="500px">
                  <v-card>
                    <v-card-title class="headline">You really want to dispose of that?</v-card-title>
                    <v-card-actions>
                      <v-spacer></v-spacer>
                      <v-btn color="secondary darken-1" text @click="closeDelete">Let mercy rule.</v-btn>
                      <v-btn color="warning accent-1" text @click="deleteConfirm">Get it out of my sight.</v-btn>
                    </v-card-actions>
                  </v-card>
                </v-dialog>
                <v-btn 
                  id="refresh" 
                  class="ml-2"
                  dense depressed 
                  @click="loadUsers()"><v-icon>mdi-refresh</v-icon></v-btn>
              </v-toolbar>
            </template>
            <template v-slot:item.lastname="{ item }">
              {{item.firstname}} {{item.lastname}}
            </template>
            <template v-slot:item.isActive="{ item }">
              <v-icon small>{{item.isActive ? 'mdi-check' : 'mdi-minus'}}</v-icon>
            </template>
            <template v-slot:item.isAdmin="{ item }">
              <v-icon :small="!item.isAdmin">{{item.isAdmin ? 'mdi-wizard-hat' : 'mdi-minus'}}</v-icon>
            </template>
            <template v-slot:item.actions="{ item }">
              <v-icon
                small
                class="mr-2"
                @click="editUser(item)">
                mdi-pencil
              </v-icon>
              <v-icon
                small
                @click="deleteUser(item)">
                mdi-delete
              </v-icon>
            </template>
          </v-data-table>
        </v-col>
      </v-row>
    </v-container>
  </div>
  
</template>
<script lang="ts">
import { User } from '@/store/models';
import Vue from 'vue';
import { DataTableHeader } from 'vuetify';
import { cloneDeep as _cloneDeep, find as _find } from 'lodash';

interface State {
  search: string;
  sortBy: string;
  sortDesc: boolean;
  editItem: User;
  showEdit: boolean;
  showDelete: boolean;
  passwordVisible: boolean;
  password1: string;
  password2: string;
  editValid: boolean;
}

function defaultItem(): User {
  const user = new User();
  user.createdAt = new Date();
  user.isActive = true;
  user.isAdmin = false;
  user.source = 'local';
  return user;
}

export default Vue.extend({
  name: 'Users',
  mounted() {
    this.loadUsers().then(() => this.openEdit(this.$route.query.id));
  },
  data: (): { headers: DataTableHeader[]; localState: State } => ({
    headers: [
      { text: 'id', value: 'id', sortable: true, filterable: false, width: '5%' },
      { text: 'Username', value: 'username', sortable: true, filterable: true, width: '15%' },
      { text: 'Email', value: 'email', sortable: true, filterable: true, width: '15%' },
      { text: 'Name', value: 'lastname', sortable: true, filterable: true, width: '', },
      { text: 'Admin', value: 'isAdmin', sortable: true, filterable: false, width: '5%' },
      { text: 'Active', value: 'isActive', sortable: true, filterable: false, width: '5%' },
      { text: 'Source', value: 'source', sortable: true, filterable: true, width: '9%' },
      { text: 'Actions', value: 'actions', sortable: false, filterable: false, width: '1%' },
    ],
    localState: {
      search: '',
      sortBy: 'id',
      sortDesc: false,
      editValid: true,
      editItem: defaultItem(),
      showEdit: false,
      showDelete: false,
      passwordVisible: false,
      password1: '',
      password2: '',
    },
  }),
  computed: {
    users() {
      return this.$store.getters['users/list'];
    },
    loading() {
      return this.$store.getters['users/status']==='loading';
    },
    editTitle(): string {
      return this.localState.editItem.id ? 'Edit User' : 'Create User';
    },
    passwordsMatching(): boolean {
      return this.localState.password1 === this.localState.password2;
    },
    currentUser(): User {
      return this.$store.getters['currentUser'];
    },
  },
  watch: {
    'localState.showEdit': function showEdit(val) {
      if (!val) {
        if (this.$route.query.id) {
          this.$router.push({ query: { id: undefined }});
        }
        this._closeEdit();
      }
    },
    'localState.showDelete': function showDelete(val) {
      if (!val) {
        this.closeDelete();
        this.$nextTick(() => {
          this.localState.editItem = defaultItem();
        });
      }
    },
    '$route.query.id': function openEditUser(id) {
      this.openEdit(id);
    },
  },
  methods: {
    loadUsers(): Promise<User[]> {
      return this.$store.dispatch('users/list')
        .catch(err => this.$store.commit('snackbar/showError', err));
    },
    openEdit(id: string | (string | null)[]) {
      if (id) {
        const user = _find(this.users, u => u.id === id || u.username === id);
        if (user) {
          this._editUser(user);
        }
        else {
          console.log(`${id} not found`);
        }
      }
      else {
        this.localState.showEdit=false;
      }
    },
    closeEdit() {
      this.localState.showEdit = false;
    },
    _closeEdit() {
      this.$nextTick(() => {
        this.localState.editItem = defaultItem();
        this.localState.password1 = '';
        this.localState.password2 = '';
      });
    },
    editUser(user: User) {
      this.$router.push({ query: { id: user.id }});
    },
    _editUser(user: User) {
      this.localState.editItem = _cloneDeep(user);
      this.localState.showEdit = true;
    },
    deleteUser(user: User) {
      this.localState.editItem = _cloneDeep(user);
      this.localState.showDelete = true;
    },
    closeDelete() {
      this.localState.showDelete = false;
    },
    save() {
      const action = this.localState.editItem.id ?
        'users/update' : 'users/create';

      if (this.localState.password1 && this.passwordsMatching===true) {
        this.localState.editItem.password = this.localState.password1;
      }
      this.$store.dispatch(action, this.localState.editItem)
        .then(() => this.$store.commit('snackbar/showSuccess', 'Hoorary!'))
        .catch(err => this.$store.commit('snackbar/showError', err));
      this.closeEdit();
    },
    deleteConfirm() {
      this.$store.dispatch('users/delete', this.localState.editItem)
        .then(() => this.$store.commit('snackbar/showSuccess', "It's gone!"))
        .catch(err => this.$store.commit('snackbar/showError', err));
      this.closeDelete();
    },
  },
});
</script>